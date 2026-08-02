для добавления новой камеры:
- создать класс камеры в utils/Classes (наследник AbstractCamera)
  и повесить декоратор `@register_camera(typ="...", title="...")` из utils/Classes/CameraRegistry.py
- создать конфиг-страницу в utils/Menus/CameraTypeConfig.py
  и повесить декоратор `@register_camera_config(typ="...", title="...")` (typ должен совпадать)

Больше ничего трогать не нужно:
- классы камер подхватываются автоматически (CameraRegistry.discover_cameras)
- фабрика и меню подключения строятся из единого CAMERA_REGISTRY

если у камеры нестандартная сборка из конфига (не все ключи конфига идут в __init__),
передай в register_camera аргумент build=lambda config: CamCls(...)
