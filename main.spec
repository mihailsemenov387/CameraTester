# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

# Эта магия автоматически найдет все .py файлы внутри папки workspaces
# и скажет PyInstaller'у скомпилировать их в байт-код.
# Теперь, если вы добавите новый воркспейс, .spec файл менять НЕ ПРИДЕТСЯ!
dynamic_workspaces = collect_submodules("workspaces")

a = Analysis(
    ["src/main.py"],
    pathex=[".", "src"],  # Пути поиска импортов
    binaries=[],
    # ВНИМАНИЕ: Папки с исходным кодом (.py) здесь быть не должно!
    # datas нужен только если в папке workspaces есть НЕ-код (например, иконки .png).
    # Если там только код, оставляем список пустым.
    datas=[],
    hiddenimports=[
        "shiboken6",
        # Явные зависимости из utils (оставляем для надежности)
        "utils",
        "utils.Classes.AbstractCamera",
        "utils.Widgets.VideoDisplayWidget",
        "utils.Signals",
        # Ручной импорт камеры (хотя при "from .CameraWorkspace.workspace import..."
        # в MainWindow PyInstaller должен находить её сам, но оставим для страховки)
        "src.CameraWorkspace.workspace",
        "src.CameraWorkspace.CameraSettingsWidget",
    ]
    + dynamic_workspaces,  # <--- Динамически добавляем все воркспейсы в скрытые импорты
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
