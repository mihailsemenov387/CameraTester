# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ["src/main.py"],
    pathex=[".", "src"],
    binaries=[],
    datas=[
        ("src/CameraWorkspace", "src/CameraWorkspace"),
        ("workspaces", "workspaces"),
    ],
    hiddenimports=[
        "shiboken6",
        "utils",
        "utils.Classes",
        "utils.Classes.AbstractCamera",
        "utils.Widgets",
        "utils.Widgets.VideoDisplayWidget",
        "utils.Signals",
        "CameraWorkspace",
        "CameraWorkspace.workspace",
        "CameraWorkspace.CameraSettingsWidget",
        "workspaces",
        "workspaces.AnalysisWorkspace",
        "workspaces.AnalysisWorkspace.workspace",
    ],
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
    console=False,
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
