import cv2
import numpy as np
from harvesters.core import Harvester

from .AbstractCamera import AbstractCamera, CameraParameter


class HarvesterCamera(AbstractCamera):
    def __init__(self, cti_path: str, serial: str = None):
        self.cti_path = cti_path
        self.serial = serial
        self.harvester = Harvester()
        self.ia = None

    def open(self) -> bool:
        try:
            self.harvester.add_file(self.cti_path)
            self.harvester.update()
            self.ia = self.harvester.create(0)

            nodemap = self.ia.remote_device.node_map
            if hasattr(nodemap, "ExposureTime"):
                self.exp_min = int(nodemap.ExposureTime.min)
                self.exp_max = int(nodemap.ExposureTime.max)
                self.exp_curr = int(nodemap.ExposureTime.value)

            self.ia.start()
            return True
        except Exception:
            return False

    def get_frame(self) -> np.ndarray:
        if not self.ia:
            return None

        try:
            with self.ia.fetch(timeout=10) as buffer:
                payload = buffer.payload
                if not payload or len(payload.components) == 0:
                    return None

                component = payload.components[0]
                width = component.width
                height = component.height

                data = component.data.reshape(height, width).copy()

                return data

        except Exception as e:
            print(f"[DEBUG] Ошибка в get_frame: {e}")
            return None

    def get_fps(self):
        return 30.0

    def set_exposure(self, value: int):
        if self.ia:
            self.ia.remote_device.node_map.ExposureTime.value = float(value)

    def set_gain(self, value: int):
        if self.ia:
            self.ia.remote_device.node_map.Gain.value = float(value)

    def set_brightness(self, value):
        pass

    def set_contrast(self, value):
        pass

    def set_gamma(self, value):
        pass

    def set_auto_exposure(self, is_auto):
        pass

    def close(self):
        if self.ia:
            self.ia.stop()
            self.ia.destroy()
            self.ia = None
        self.harvester.reset()

    def get_parameters(self) -> dict:
        if not self.ia:
            return {}

        nodemap = self.ia.remote_device.node_map
        params = {}

        if hasattr(nodemap, "ExposureTime"):
            exp_node = nodemap.ExposureTime
            params["exposure"] = CameraParameter(
                id="exposure",
                label="Экспозиция (мкс):",
                min_value=int(exp_node.min),
                max_value=int(exp_node.max),
                default_value=int(exp_node.min),
                current_value=int(exp_node.value),
                setter=self.set_exposure,
            )

        gain_attr = None
        for attr_name in ["Gain", "GainRaw", "GaindB"]:
            if hasattr(nodemap, attr_name):
                gain_attr = attr_name
                break

        if gain_attr:
            gain_node = getattr(nodemap, gain_attr)
            params["gain"] = CameraParameter(
                id="gain",
                label="Gain (дБ):",
                min_value=int(gain_node.min),
                max_value=int(gain_node.max),
                default_value=int(gain_node.min),
                current_value=int(gain_node.value),
                setter=self.set_gain,
            )

        return params
