import numpy as np
from PySide6.QtGui import QImage

from utils.Classes.AbstractCamera import CameraThread
from utils.SpecialFunctions.AnalysysFun import fit_gaussian, gauss, process


class FrameAnalyzer:
    def __init__(self, camera_thread: CameraThread) -> None:
        self.camera_thread = camera_thread
        self.camera_thread.frame_ready.connect(self.AnalyseFrame)

    def AnalyseFrame(self, qimg: QImage):
        img = self.qimage_to_ndarray(qimg)
        results = process(img)

    def qimage_to_ndarray(self, img: QImage) -> np.ndarray:
        # 1. Обязательно переводим в стандартный формат (например, 32-битный RGBA),
        # чтобы избежать проблем с выравниванием пикселей в памяти
        qimage = img.convertToFormat(QImage.Format.Format_RGBA8888)

        width = qimage.width()
        height = qimage.height()

        # 2. Получаем доступ к буферу памяти
        # В PySide6/PyQt6 это делается через bits().asstring()
        ptr = qimage.bits()
        buffer = ptr.asstring(qimage.sizeInBytes())

        # 3. Создаем numpy массив из буфера
        arr = np.frombuffer(buffer, dtype=np.uint8)

        # 4. Меняем форму под размеры картинки (высота, ширина, 4 канала RGBA)
        return arr.reshape((height, width, 4))
