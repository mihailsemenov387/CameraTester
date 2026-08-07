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

---

## Point Grey / FlyCapture2 (старые монохромные камеры: Chameleon, FireFly...)

Старые USB 2.0 камеры Point Grey не поддерживают GenICam/cti и работают только
через SDK FlyCapture2. Подключение через тонкий ctypes-адаптер:

- `utils/Classes/FlyCapture2Native.py` — привязки к C API `fc2_*`
  (Windows: `FlyCapture2C.dll`, Linux: `libflycapture-c.so`).
  Layout структур взят из заголовков SDK 2.13.x (`include/C/FlyCapture2*_C.h`).
- `utils/Classes/PointGreyCamera.py` — класс камеры (тип `POINTGREY`).

Где берётся SDK:
- Windows — официальный инсталлятор FlyCapture2 SDK (архив FLIR:
  https://flir.app.boxcn.net/v/Flycapture2SDK ), он ставит DLL + USB-драйвер.
- Linux — пакеты `lbl-anp/flycapture2_sdk` (Ubuntu .deb: `libflycapture-c`).

Поиск библиотеки: переменные окружения `FLYCAPTURE2_SDK`/`FLYCAPTURE2_LIB`,
папки `External/` и корень проекта, стандартные пути установки, системные пути.
Можно просто положить `FlyCapture2C.dll` (+ зависимые DLL) в `External/`.

Если SDK не установлен — тип камеры остаётся в меню, но конфиг-страница
покажет «SDK не найден», а подключение честно завершится с ошибкой.

