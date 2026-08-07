"""Тонкий ctypes-адаптер над C API библиотеки FlyCapture2 (fc2_*).

Загружает FlyCapture2C.dll (Windows) / libflycapture-c.so (Linux) и
предоставляет Python-обёртки над нужными функциями и структурами.
Если SDK не установлен, модуль не падает: available() возвращает False,
а list_cameras() возвращает None.

Layout структур и значения перечислений взяты из официальных заголовков
FlyCapture2Defs_C.h / FlyCapture2_C.h (SDK 2.13.x).
"""
import ctypes
import ctypes.util
import os
import sys
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_char,
    c_float,
    c_int,
    c_ubyte,
    c_uint,
    c_void_p,
)
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- fc2PropertyType ---
FC2_BRIGHTNESS = 0
FC2_AUTO_EXPOSURE = 1
FC2_SHARPNESS = 2
FC2_WHITE_BALANCE = 3
FC2_HUE = 4
FC2_SATURATION = 5
FC2_GAMMA = 6
FC2_IRIS = 7
FC2_FOCUS = 8
FC2_ZOOM = 9
FC2_PAN = 10
FC2_TILT = 11
FC2_SHUTTER = 12
FC2_GAIN = 13
FC2_TRIGGER_MODE = 14
FC2_TRIGGER_DELAY = 15
FC2_FRAME_RATE = 16
FC2_TEMPERATURE = 17

# --- fc2PixelFormat (значения в виде знаковых int) ---
FC2_PIXEL_FORMAT_MONO8 = -2147483648      # 0x80000000
FC2_PIXEL_FORMAT_RGB8 = 0x08000000
FC2_PIXEL_FORMAT_MONO16 = 0x04000000
FC2_PIXEL_FORMAT_RAW8 = 0x00400000
FC2_PIXEL_FORMAT_BGR = -2147483640        # 0x80000008

# --- fc2BayerTileFormat ---
FC2_BT_NONE = 0

# --- fc2Error ---
FC2_ERROR_OK = 0
FC2_ERROR_TIMEOUT = 18

_FC2_ERRORS = {
    -1: "FC2_ERROR_UNDEFINED",
    0: "FC2_ERROR_OK",
    1: "FC2_ERROR_FAILED",
    2: "FC2_ERROR_NOT_IMPLEMENTED",
    3: "FC2_ERROR_FAILED_BUS_MASTER_CONNECTION",
    4: "FC2_ERROR_NOT_CONNECTED",
    5: "FC2_ERROR_INIT_FAILED",
    6: "FC2_ERROR_NOT_INTITIALIZED",
    7: "FC2_ERROR_INVALID_PARAMETER",
    8: "FC2_ERROR_INVALID_SETTINGS",
    9: "FC2_ERROR_INVALID_BUS_MANAGER",
    10: "FC2_ERROR_MEMORY_ALLOCATION_FAILED",
    11: "FC2_ERROR_LOW_LEVEL_FAILURE",
    12: "FC2_ERROR_NOT_FOUND",
    13: "FC2_ERROR_FAILED_GUID",
    14: "FC2_ERROR_INVALID_PACKET_SIZE",
    15: "FC2_ERROR_INVALID_MODE",
    16: "FC2_ERROR_NOT_IN_FORMAT7",
    17: "FC2_ERROR_NOT_SUPPORTED",
    18: "FC2_ERROR_TIMEOUT",
    19: "FC2_ERROR_BUS_MASTER_FAILED",
    20: "FC2_ERROR_INVALID_GENERATION",
    21: "FC2_ERROR_LUT_FAILED",
    22: "FC2_ERROR_IIDC_FAILED",
    23: "FC2_ERROR_STROBE_FAILED",
    24: "FC2_ERROR_TRIGGER_FAILED",
    25: "FC2_ERROR_PROPERTY_FAILED",
    26: "FC2_ERROR_PROPERTY_NOT_PRESENT",
    27: "FC2_ERROR_REGISTER_FAILED",
    28: "FC2_ERROR_READ_REGISTER_FAILED",
    29: "FC2_ERROR_WRITE_REGISTER_FAILED",
    30: "FC2_ERROR_ISOCH_FAILED",
    31: "FC2_ERROR_ISOCH_ALREADY_STARTED",
    32: "FC2_ERROR_ISOCH_NOT_STARTED",
    33: "FC2_ERROR_ISOCH_START_FAILED",
    34: "FC2_ERROR_ISOCH_RETRIEVE_BUFFER_FAILED",
    35: "FC2_ERROR_ISOCH_STOP_FAILED",
    36: "FC2_ERROR_ISOCH_SYNC_FAILED",
    37: "FC2_ERROR_ISOCH_BANDWIDTH_EXCEEDED",
    38: "FC2_ERROR_IMAGE_CONVERSION_FAILED",
    39: "FC2_ERROR_IMAGE_LIBRARY_FAILURE",
    40: "FC2_ERROR_BUFFER_TOO_SMALL",
    41: "FC2_ERROR_IMAGE_CONSISTENCY_ERROR",
    42: "FC2_ERROR_INCOMPATIBLE_DRIVER",
}


# --- Структуры C API ---

class fc2PGRGuid(Structure):
    _fields_ = [("value", c_uint * 4)]


class fc2Image(Structure):
    _fields_ = [
        ("rows", c_uint),
        ("cols", c_uint),
        ("stride", c_uint),
        ("pData", POINTER(c_ubyte)),
        ("dataSize", c_uint),
        ("receivedDataSize", c_uint),
        ("format", c_int),
        ("bayerFormat", c_int),
        ("imageImpl", c_void_p),
    ]


class fc2Property(Structure):
    _fields_ = [
        ("type", c_int),
        ("present", c_int),
        ("absControl", c_int),
        ("onePush", c_int),
        ("onOff", c_int),
        ("autoManualMode", c_int),
        ("valueA", c_uint),
        ("valueB", c_uint),
        ("absValue", c_float),
        ("reserved", c_uint * 8),
    ]


class fc2PropertyInfo(Structure):
    _fields_ = [
        ("type", c_int),
        ("present", c_int),
        ("autoSupported", c_int),
        ("manualSupported", c_int),
        ("onOffSupported", c_int),
        ("onePushSupported", c_int),
        ("absValSupported", c_int),
        ("readOutSupported", c_int),
        ("min", c_uint),
        ("max", c_uint),
        ("absMin", c_float),
        ("absMax", c_float),
        ("pUnits", c_char * 512),
        ("pUnitAbbr", c_char * 512),
        ("reserved", c_uint * 8),
    ]


class fc2Config(Structure):
    _fields_ = [
        ("numBuffers", c_uint),
        ("numImageNotifications", c_uint),
        ("minNumImageNotifications", c_uint),
        ("grabTimeout", c_int),
        ("grabMode", c_int),
        ("highPerformanceRetrieveBuffer", c_int),
        ("isochBusSpeed", c_int),
        ("asyncBusSpeed", c_int),
        ("bandwidthAllocation", c_int),
        ("registerTimeoutRetries", c_uint),
        ("registerTimeout", c_uint),
        ("reserved", c_uint * 16),
    ]


# fc2CameraInfo описан частично (до modelName включительно): этого хватает,
# чтобы читать serialNumber и modelName. Полная структура (~5 КБ) пишется
# библиотекой в большой буфер, который мы передаём в fc2GetCameraInfo().
class fc2CameraInfo(Structure):
    _fields_ = [
        ("serialNumber", c_uint),
        ("interfaceType", c_int),
        ("driverType", c_int),
        ("isColorCamera", c_int),
        ("modelName", c_char * 512),
        ("vendorName", c_char * 512),
    ]


# --- Поиск и загрузка библиотеки ---

def _candidate_paths():
    """Список путей к библиотеке C API FlyCapture2."""
    if sys.platform == "win32":
        names = ("FlyCapture2C.dll",)
        roots = [
            os.environ.get("FLYCAPTURE2_SDK", ""),
            os.environ.get("FLYCAPTURE2_LIB", ""),
            str(PROJECT_ROOT / "External"),
            str(PROJECT_ROOT),
            r"C:\Program Files\Point Grey Research\FlyCapture2",
            r"C:\Program Files\FLIR\FlyCapture2",
        ]
    else:
        names = ("libflycapture-c.so", "libflycapture-c.so.2")
        roots = [
            os.environ.get("FLYCAPTURE2_SDK", ""),
            os.environ.get("FLYCAPTURE2_LIB", ""),
            str(PROJECT_ROOT / "External"),
            str(PROJECT_ROOT),
            "/usr/local/lib",
            "/usr/lib",
        ]

    found = []
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
                    found.append(p)
    # Рекурсивный поиск внутри External (SDK может лежать глубже)
    ext = PROJECT_ROOT / "External"
    if ext.is_dir():
        for p in ext.rglob("*"):
            if p.is_file() and p.name in names:
                found.append(p)
    return found


_lib = None
_library_path = None
sdk_missing_reason = "SDK FlyCapture2 не найден"

for _path in _candidate_paths():
    try:
        if sys.platform == "win32":
            _lib = ctypes.WinDLL(str(_path))
        else:
            _lib = ctypes.CDLL(str(_path))
        _library_path = str(_path)
        break
    except OSError as e:
        sdk_missing_reason = f"Не удалось загрузить {_path}: {e}"
        _lib = None

if _lib is None and not sys.platform.startswith("win"):
    try:
        lib_name = ctypes.util.find_library("flycapture-c") or "libflycapture-c.so"
        _lib = ctypes.CDLL(lib_name)
        _library_path = lib_name
    except OSError as e:
        sdk_missing_reason = f"Не удалось загрузить {getattr(e, 'filename', 'libflycapture-c')}: {e}"

if _lib is None and sys.platform == "win32":
    try:
        _lib = ctypes.WinDLL("FlyCapture2C.dll")
        _library_path = "FlyCapture2C.dll"
    except OSError as e:
        sdk_missing_reason = f"FlyCapture2C.dll не найден: {e}"


def available():
    return _lib is not None


def library_path():
    return _library_path


def _bind(name, restype, argtypes):
    func = getattr(_lib, name)
    func.restype = restype
    func.argtypes = argtypes
    return func


def error_name(ret):
    return _FC2_ERRORS.get(ret, f"unknown ({ret})")


def check(ret):
    """Бросает RuntimeError, если fc2-функция вернула не OK."""
    if ret != FC2_ERROR_OK:
        raise RuntimeError(f"FlyCapture2 error {ret}: {error_name(ret)}")


# --- Привязка функций (только если библиотека загружена) ---

fc2CreateContext = fc2DestroyContext = fc2GetNumOfCameras = None
fc2GetCameraFromIndex = fc2GetCameraFromSerialNumber = None
fc2GetCameraInfo = fc2Connect = fc2Disconnect = None
fc2StartCapture = fc2StopCapture = fc2RetrieveBuffer = None
fc2GetConfiguration = fc2SetConfiguration = None
fc2GetProperty = fc2SetProperty = fc2GetPropertyInfo = None
fc2CreateImage = fc2DestroyImage = None
fc2SetImageDimensions = fc2SetImageData = fc2ConvertImageTo = None

if _lib is not None:
    fc2CreateContext = _bind("fc2CreateContext", c_int, [POINTER(c_void_p)])
    fc2DestroyContext = _bind("fc2DestroyContext", c_int, [c_void_p])
    fc2GetNumOfCameras = _bind("fc2GetNumOfCameras", c_int, [c_void_p, POINTER(c_uint)])
    fc2GetCameraFromIndex = _bind("fc2GetCameraFromIndex", c_int, [c_void_p, c_uint, POINTER(fc2PGRGuid)])
    fc2GetCameraFromSerialNumber = _bind("fc2GetCameraFromSerialNumber", c_int, [c_void_p, c_uint, POINTER(fc2PGRGuid)])
    fc2GetCameraInfo = _bind("fc2GetCameraInfo", c_int, [c_void_p, POINTER(fc2CameraInfo)])
    fc2Connect = _bind("fc2Connect", c_int, [c_void_p, POINTER(fc2PGRGuid)])
    fc2Disconnect = _bind("fc2Disconnect", c_int, [c_void_p])
    fc2StartCapture = _bind("fc2StartCapture", c_int, [c_void_p])
    fc2StopCapture = _bind("fc2StopCapture", c_int, [c_void_p])
    fc2RetrieveBuffer = _bind("fc2RetrieveBuffer", c_int, [c_void_p, POINTER(fc2Image)])
    fc2GetConfiguration = _bind("fc2GetConfiguration", c_int, [c_void_p, POINTER(fc2Config)])
    fc2SetConfiguration = _bind("fc2SetConfiguration", c_int, [c_void_p, POINTER(fc2Config)])
    fc2GetProperty = _bind("fc2GetProperty", c_int, [c_void_p, POINTER(fc2Property)])
    fc2SetProperty = _bind("fc2SetProperty", c_int, [c_void_p, POINTER(fc2Property)])
    fc2GetPropertyInfo = _bind("fc2GetPropertyInfo", c_int, [c_void_p, POINTER(fc2PropertyInfo)])
    fc2CreateImage = _bind("fc2CreateImage", c_int, [POINTER(fc2Image)])
    fc2DestroyImage = _bind("fc2DestroyImage", c_int, [POINTER(fc2Image)])
    fc2SetImageDimensions = _bind("fc2SetImageDimensions", c_int, [POINTER(fc2Image), c_uint, c_uint, c_uint, c_int, c_int])
    fc2SetImageData = _bind("fc2SetImageData", c_int, [POINTER(fc2Image), POINTER(c_ubyte), c_uint])
    fc2ConvertImageTo = _bind("fc2ConvertImageTo", c_int, [c_int, POINTER(fc2Image), POINTER(fc2Image)])


def list_cameras():
    """Возвращает список [(model, serial), ...] или None, если SDK не загружен."""
    if _lib is None:
        return None

    ctx = c_void_p()
    check(fc2CreateContext(byref(ctx)))
    try:
        num = c_uint(0)
        check(fc2GetNumOfCameras(ctx, byref(num)))

        out = []
        for i in range(num.value):
            guid = fc2PGRGuid()
            check(fc2GetCameraFromIndex(ctx, i, byref(guid)))
            check(fc2Connect(ctx, byref(guid)))
            info = _camera_info(ctx)
            fc2Disconnect(ctx)
            if info is None:
                continue
            model, serial = info
            out.append((model, serial))
        return out
    finally:
        fc2DestroyContext(ctx)


def _camera_info(ctx):
    """Возвращает (model, serial) подключённой камеры или None."""
    buf = ctypes.create_string_buffer(16384)
    p_info = ctypes.cast(buf, POINTER(fc2CameraInfo))
    if fc2GetCameraInfo(ctx, p_info) != FC2_ERROR_OK:
        return None
    info = p_info.contents
    model = info.modelName.decode("utf-8", errors="replace").strip("\x00 ")
    return model or "Point Grey", int(info.serialNumber)
