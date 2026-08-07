import ctypes
from ctypes import POINTER, byref, c_ubyte, c_uint, c_void_p

import numpy as np

from . import FlyCapture2Native as fc2n
from .AbstractCamera import AbstractCamera, CameraParameter
from .CameraRegistry import register_camera


@register_camera(typ="POINTGREY", title="Point Grey / FlyCapture2")
class PointGreyCamera(AbstractCamera):
    """Старые монохромные камеры Point Grey (Chameleon, FireFly, ...) USB 2.0
    через C API библиотеки FlyCapture2 (FlyCapture2C.dll / libflycapture-c.so).
    GenICam/cti такие камеры не поддерживают, поэтому идём через SDK.
    """

    def __init__(self, serial=None):
        self.serial = int(serial) if serial not in (None, "") else None
        self._ctx = None
        self._p_src = None
        self._p_dst = None

    # ------------------------------------------------------------------ #
    # Служебные
    # ------------------------------------------------------------------ #
    def _require_sdk(self):
        if not fc2n.available():
            raise RuntimeError(fc2n.sdk_missing_reason)

    def open(self) -> bool:
        try:
            self._require_sdk()
        except RuntimeError as e:
            print(f"[POINTGREY] {e}")
            return False

        try:
            ctx = c_void_p()
            fc2n.check(fc2n.fc2CreateContext(byref(ctx)))
            self._ctx = ctx

            guid = fc2n.fc2PGRGuid()
            if self.serial is not None:
                fc2n.check(fc2n.fc2GetCameraFromSerialNumber(ctx, self.serial, byref(guid)))
            else:
                num = c_uint(0)
                fc2n.check(fc2n.fc2GetNumOfCameras(ctx, byref(num)))
                if num.value == 0:
                    print("[POINTGREY] Камеры не найдены")
                    self.close()
                    return False
                fc2n.check(fc2n.fc2GetCameraFromIndex(ctx, 0, byref(guid)))

            fc2n.check(fc2n.fc2Connect(ctx, byref(guid)))

            # Таймаут RetrieveBuffer, чтобы поток не завис навсегда при
            # отключении камеры.
            cfg = fc2n.fc2Config()
            fc2n.check(fc2n.fc2GetConfiguration(ctx, byref(cfg)))
            cfg.grabTimeout = 1000
            fc2n.check(fc2n.fc2SetConfiguration(ctx, byref(cfg)))

            self._p_src = ctypes.cast(
                ctypes.create_string_buffer(256), POINTER(fc2n.fc2Image)
            )
            fc2n.check(fc2n.fc2CreateImage(self._p_src))

            self._p_dst = ctypes.cast(
                ctypes.create_string_buffer(256), POINTER(fc2n.fc2Image)
            )
            fc2n.check(fc2n.fc2CreateImage(self._p_dst))

            fc2n.check(fc2n.fc2StartCapture(ctx))
            return True
        except Exception as e:
            print(f"[POINTGREY] Ошибка открытия: {e}")
            self.close()
            return False

    def get_frame(self) -> np.ndarray:
        if self._ctx is None:
            return None

        ret = fc2n.fc2RetrieveBuffer(self._ctx, self._p_src)
        if ret != fc2n.FC2_ERROR_OK:
            return None

        img = self._p_src.contents
        rows, cols = int(img.rows), int(img.cols)
        if rows <= 0 or cols <= 0:
            return None

        # Моно-камеру переводим в BGR (3 канала), как остальные камеры в проекте.
        out = np.empty((rows, cols, 3), dtype=np.uint8)
        ptr = out.ctypes.data_as(POINTER(c_ubyte))
        fc2n.check(
            fc2n.fc2SetImageDimensions(
                self._p_dst, rows, cols, cols * 3, fc2n.FC2_PIXEL_FORMAT_BGR, fc2n.FC2_BT_NONE
            )
        )
        fc2n.check(fc2n.fc2SetImageData(self._p_dst, ptr, out.nbytes))
        fc2n.check(fc2n.fc2ConvertImageTo(fc2n.FC2_PIXEL_FORMAT_BGR, self._p_src, self._p_dst))
        return out

    def get_fps(self) -> float:
        return 30.0

    # ------------------------------------------------------------------ #
    # Свойства камеры
    # ------------------------------------------------------------------ #
    def _set_prop(self, prop_type, abs_value=None, auto=None):
        p = fc2n.fc2Property()
        p.type = prop_type
        if abs_value is not None:
            p.absControl = 1
            p.absValue = float(abs_value)
        if auto is not None:
            p.autoManualMode = 1 if auto else 0
        fc2n.check(fc2n.fc2SetProperty(self._ctx, byref(p)))

    def set_exposure(self, value):
        if self._ctx is not None:
            self._set_prop(fc2n.FC2_SHUTTER, abs_value=value)

    def set_gain(self, value):
        if self._ctx is not None:
            self._set_prop(fc2n.FC2_GAIN, abs_value=value)

    def set_auto_exposure(self, is_auto):
        if self._ctx is not None:
            self._set_prop(fc2n.FC2_AUTO_EXPOSURE, auto=is_auto)

    def set_brightness(self, value):
        pass

    def set_contrast(self, value):
        pass

    def set_gamma(self, value):
        pass

    def get_parameters(self) -> dict:
        if self._ctx is None:
            return {}

        params = {}

        def _query(prop_type):
            info = fc2n.fc2PropertyInfo()
            info.type = prop_type
            if fc2n.fc2GetPropertyInfo(self._ctx, byref(info)) != 0 or not info.present:
                return None
            cur = fc2n.fc2Property()
            cur.type = prop_type
            cur.absControl = 1
            if fc2n.fc2GetProperty(self._ctx, byref(cur)) != 0:
                return None
            return info, cur

        item = _query(fc2n.FC2_SHUTTER)
        if item:
            info, cur = item
            params["exposure"] = CameraParameter(
                id="exposure",
                label="Экспозиция (мкс):",
                min_value=int(info.absMin),
                max_value=int(info.absMax),
                default_value=int(info.absMin),
                current_value=int(cur.absValue),
                setter=self.set_exposure,
                has_auto=True,
                auto_setter=self.set_auto_exposure,
            )

        item = _query(fc2n.FC2_GAIN)
        if item:
            info, cur = item
            params["gain"] = CameraParameter(
                id="gain",
                label="Gain (дБ):",
                min_value=int(info.absMin),
                max_value=int(info.absMax),
                default_value=int(info.absMin),
                current_value=int(cur.absValue),
                setter=self.set_gain,
            )

        return params

    def close(self):
        if self._ctx is not None:
            try:
                fc2n.fc2StopCapture(self._ctx)
            except Exception:
                pass
            try:
                if self._p_src is not None:
                    fc2n.fc2DestroyImage(self._p_src)
                if self._p_dst is not None:
                    fc2n.fc2DestroyImage(self._p_dst)
            except Exception:
                pass
            try:
                fc2n.fc2Disconnect(self._ctx)
                fc2n.fc2DestroyContext(self._ctx)
            except Exception:
                pass
        self._ctx = None
        self._p_src = None
        self._p_dst = None


def list_point_grey_cameras():
    """Для конфиг-страницы: список [(model, serial)] или None, если SDK нет."""
    return fc2n.list_cameras()
