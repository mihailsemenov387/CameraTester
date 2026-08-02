import importlib
import pkgutil
from typing import Any, Callable, Optional

# Единый реестр камер. Класс камеры и конфиг-страница регистрируются
# по одному и тому же ключу (typ) через декораторы ниже.
CAMERA_REGISTRY = {}


class CameraEntry:
    def __init__(self, typ: str, title: str):
        self.typ = typ
        self.title = title
        self.camera_cls: Optional[type] = None
        self.config_cls: Optional[type] = None
        self.build: Optional[Callable[[dict], Any]] = None

    def is_complete(self) -> bool:
        return self.camera_cls is not None and self.config_cls is not None

    def create(self, config: dict) -> Any:
        if self.build is not None:
            return self.build(config)
        # По умолчанию передаём в __init__ все ключи конфига, кроме служебных.
        kwargs = {k: v for k, v in config.items() if k not in ("type", "name")}
        return self.camera_cls(**kwargs)


def register_camera(
    typ: str,
    title: str,
    build: Optional[Callable[[dict], Any]] = None,
):
    """Декоратор для класса камеры. Пример:
    @register_camera(typ="UVC", title="USB Camera (UVC)")
    class UVCCamera(AbstractCamera): ...
    """

    def wrapper(cls):
        entry = CAMERA_REGISTRY.setdefault(typ, CameraEntry(typ, title))
        entry.title = title
        entry.camera_cls = cls
        entry.build = build
        return cls

    return wrapper


def register_camera_config(typ: str, title: str):
    """Декоратор для конфиг-страницы камеры. Должен совпадать по typ с классом."""

    def wrapper(cls):
        entry = CAMERA_REGISTRY.setdefault(typ, CameraEntry(typ, title))
        entry.title = title
        entry.config_cls = cls
        return cls

    return wrapper


def create_camera(config: dict) -> Optional[Any]:
    entry = CAMERA_REGISTRY.get(config.get("type"))
    if entry is None or entry.camera_cls is None:
        return None
    return entry.create(config)


def discover_cameras():
    """Автоматически импортируем все модули в utils.Classes,
    чтобы сработали декораторы register_camera."""
    import utils.Classes as classes_pkg

    prefix = classes_pkg.__name__ + "."
    for _, module_name, _ in pkgutil.walk_packages(classes_pkg.__path__, prefix):
        try:
            importlib.import_module(module_name)
        except Exception as e:
            print(f"[ERROR] Не удалось загрузить камеру {module_name}: {e}")


discover_cameras()
