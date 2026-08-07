# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_dynamic_libs,
    collect_submodules,
)

# Камеры и конфиг-страницы регистрируются динамически через декораторы
# (CameraRegistry, CameraTypeConfig), поэтому статический анализ их не видит —
# собираем их принудительно. Требуется, чтобы у utils и подпакетов были
# __init__.py (иначе collect_submodules возвращает почти пустой список).
dynamic_utils = collect_submodules("utils")
# Все воркспейсы тоже добавляются динамически.
dynamic_workspaces = collect_submodules("workspaces")
# harvesters (GenICam) тянет свои геновские биндинги и пакет genicam
# (genapi.py/gentl.py + .pyd), которые статически не находятся.
dynamic_harvesters = collect_submodules("harvesters") + collect_submodules("genicam")
# Нативные DLL GenICam (GCBase, GenApi, Log, XmlParser...) кладём рядом с .pyd.
genicam_libs = collect_dynamic_libs("genicam")


def _find_flycapture_dll():
    """Ищет библиотеку C API FlyCapture2 (Point Grey) для включения в exe.
    Если её нет при сборке — просто пропускаем (страница камеры покажет
    'SDK не найден'). Возвращает путь к .dll/.so или None."""
    if os.name == "nt":
        names = ("FlyCapture2C.dll",)
    else:
        names = ("libflycapture-c.so", "libflycapture-c.so.2")

    roots = [
        os.environ.get("FLYCAPTURE2_SDK", ""),
        os.environ.get("FLYCAPTURE2_LIB", ""),
        str(Path.cwd() / "External"),
        str(Path.cwd()),
        r"C:\Program Files\Point Grey Research\FlyCapture2",
        r"C:\Program Files\FLIR\FlyCapture2",
    ]
    for root in roots:
        if not root:
            continue
        root_p = Path(root)
        if not root_p.is_dir():
            continue
        for name in names:
            for sub in ("", "bin64", "bin", "lib", "lib64", "libs"):
                p = root_p / sub / name
                if p.is_file():
                    return str(p)
    ext = Path.cwd() / "External"
    if ext.is_dir():
        for p in ext.rglob("*"):
            if p.is_file() and p.name in names:
                return str(p)
    return None


flycapture_dll = _find_flycapture_dll()
flycapture_bins = [(flycapture_dll, ".")] if flycapture_dll else []

a = Analysis(
    ["src/main.py"],
    pathex=[".", "src"],  # Пути поиска импортов
    binaries=genicam_libs + flycapture_bins,
    # ВНИМАНИЕ: Папки с исходным кодом (.py) здесь быть не должно!
    # datas нужен только если в папке workspaces есть НЕ-код (например, иконки .png).
    # Если там только код, оставляем список пустым.
    datas=[],
    hiddenimports=[
        "shiboken6",
        # Явные зависимости из utils (оставляем для надежности)
        "utils",
        "utils.Classes.AbstractCamera",
        "utils.Classes.CameraRegistry",
        "utils.Classes.UVCCamera",
        "utils.Classes.FakeCamera",
        "utils.Classes.HarvesterCamera",
        "utils.Classes.PointGreyCamera",
        "utils.Classes.FlyCapture2Native",
        "utils.Menus.TopBarMenu",
        "utils.Menus.CameraTypeConfig",
        "utils.Signals",
        # Ручной импорт камеры (хотя при "from .CameraWorkspace.workspace import..."
        # в MainWindow PyInstaller должен находить её сам, но оставим для страховки)
        "src.CameraWorkspace.workspace",
        "src.CameraWorkspace.CameraSettingsWidget",
    ]
    + dynamic_utils  # <--- весь utils (камеры, конфиги, виджеты)
    + dynamic_workspaces  # <--- все воркспейсы
    + dynamic_harvesters,  # <--- GenICam (harvesters + genicam)
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CameraProject",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Черное окно консоли отключено
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CameraProject",
)
