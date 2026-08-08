import cv2
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

WINDOW = 1000
WIN_MULT_FIT = 1
IS_ADAPTIVE_WINDOW = 1

# TODO: big refactor


def gauss(x, A, mu, sigma, B):
    # Добавим защиту от sigma=0, чтобы не было деления на ноль
    if sigma == 0:
        sigma = 1e-6
    return A * np.exp(-((x - mu) ** 2) / (2 * sigma**2)) + B


def fit_gaussian(coords, w, window_size=WINDOW):
    # Убеждаемся, что w — это 1D массив (берем среднее по каналам, если вдруг пришло 2D)
    if w.ndim > 1:
        w = np.mean(w, axis=1)

    peak_idx = np.argmax(w)
    start = max(0, peak_idx - window_size)
    end = min(len(coords), peak_idx + window_size)

    c_wind = coords[start:end]
    w_wind = w[start:end]

    # Если данных нет или веса нулевые - возвращаем дефолт
    if len(w_wind) == 0 or np.sum(w_wind) <= 0:
        return (0, 0, 0, 1, 0)

    try:
        A = np.max(w_wind) - np.min(w_wind)
        B = np.min(w_wind)
        mu = np.average(c_wind, weights=w_wind)
        # Защита от отрицательной дисперсии
        var = np.average((c_wind - mu) ** 2, weights=w_wind)
        sigma = np.sqrt(max(0, var))

        popt, _ = curve_fit(gauss, c_wind, w_wind, p0=[A, mu, sigma, B], maxfev=2000)
        return (sigma, *popt)
    except Exception:
        # Если фиттинг не сошелся
        return (0, 0, 0, 1, 0)


def PSF_model(k, p_diff, p_aberr, const=0, f=300):
    return np.sqrt((p_diff * f / k) ** 2 + (p_aberr / ((f / k) ** 3)) ** 2 + const**2)


def fit_gaussian_many(coords, peak_idx, w, window_size):
    start = max(0, peak_idx - window_size)
    end = min(len(coords), peak_idx + window_size)

    c_wind = coords[start:end]
    w_wind = w[start:end]
    x = np.arange(start, end)

    if len(w_wind) == 0 or np.sum(w_wind) == 0:
        return None

    A = np.max(w_wind) - np.min(w_wind)
    B = np.min(w_wind)
    mu = np.average(c_wind, weights=w_wind)
    sigma = np.sqrt(np.average((c_wind - mu) ** 2, weights=w_wind))

    try:
        bounds = (
            [0, mu - window_size, 0, 0],
            [A * 2, mu + window_size, window_size * 2, np.max(w_wind)],
        )
        curve, _ = curve_fit(
            gauss, c_wind, w_wind, p0=[A, mu, sigma, B], bounds=bounds
        )
        return (sigma, x, curve)
    except Exception:
        return None


def calculate_V(signal):
    return (np.max(signal) - np.min(signal)) / (np.max(signal) + np.min(signal))


def process_peaks(coords, pr, peak_dist=40):  # peak_dist теперь в пикселях
    # 1. Поиск пиков (более мягкие условия)
    # Используем prominence (выступание над шумом) вместо жесткой высоты
    peaks, _ = find_peaks(
        pr,
        prominence=np.max(pr) * 0.1,  # Пик должен выступать хотя бы на 10% от макс.
        distance=peak_dist,
        height=np.min(pr) + (np.max(pr) - np.min(pr)) * 0.05,  # Чуть выше фона
    )

    if len(peaks) < 1:
        return None

    window = (
        int(np.median(np.diff(peaks)) / 2)
        if (len(peaks) > 1 and IS_ADAPTIVE_WINDOW)
        else 50
    )

    # Создаем массив для "суммарного" фита (линия, которая пойдет в Плоттер)
    # Заполняем его минимальным значением (фоном)
    y_total_fit = np.full_like(pr, np.min(pr))

    visual_fits = []
    valid_peaks = []

    for p in peaks:
        fit_res = fit_gaussian_many(coords, p, pr, int(window * WIN_MULT_FIT))
        if fit_res is None:
            continue

        sigma, x_range, curve_params = fit_res
        y_fit = gauss(x_range, *curve_params)

        # Накладываем этот "колокол" на общую линию для Плоттера
        # (используем np.maximum, чтобы фиты не суммировались в нахлестах, а выбирался высший)
        y_total_fit[x_range] = np.maximum(y_total_fit[x_range], y_fit)

        visual_fits.append((x_range, y_fit))
        valid_peaks.append(p)

    return {
        "raw_profile": pr,
        "total_fit": y_total_fit,  # Это пойдет в Плоттер одной линией
        "fits": visual_fits,  # Это пойдет в Оверлей на видео
        "peaks": valid_peaks,
    }


def process(img, base=None):
    """Анализ одного пика"""
    if base is None:
        base = _get_base_profiles(img)
    if not base:
        return None
    img_norm, x, y, x_w, y_w = base

    # Считаем фит
    res_x = fit_gaussian(x, x_w)  # (sigma, A, mu, sigma, B)
    res_y = fit_gaussian(y, y_w)

    # Формируем словарь, ГАРАНТИРУЯ наличие всех ключей
    return {
        "x": x,
        "y": y,
        "x_raw": x_w,
        "y_raw": y_w,
        "fits_x": [(x, gauss(x, *res_x[1:]))] if res_x[0] > 0 else [],
        "fits_y": [(y, gauss(y, *res_y[1:]))] if res_y[0] > 0 else [],
        "total_fit_x": gauss(x, *res_x[1:]),  # Для плоттера
        "total_fit_y": gauss(y, *res_y[1:]),
        "mu_x": res_x[2],
        "mu_y": res_y[2],
    }


def process_many(img, base=None):
    """Анализ множества пиков"""
    if base is None:
        base = _get_base_profiles(img)
    if not base:
        return None
    img_norm, x, y, x_w, y_w = base

    res_x = process_peaks(x, x_w)
    res_y = process_peaks(y, y_w)

    # Собираем данные. Даже если пики не найдены, x_raw должен быть!
    data = {
        "x": x,
        "y": y,
        "x_raw": x_w,
        "y_raw": y_w,
        "fits_x": res_x["fits"] if res_x else [],
        "fits_y": res_y["fits"] if res_y else [],
        "total_fit_x": res_x["total_fit"] if res_x else np.zeros_like(x_w),
        "total_fit_y": res_y["total_fit"] if res_y else np.zeros_like(y_w),
        "mu_x": res_x["peaks"][0] if (res_x and res_x["peaks"]) else 0,
        "mu_y": res_y["peaks"][0] if (res_y and res_y["peaks"]) else 0,
    }
    return data


def _get_base_profiles(img):
    if img is None:
        return None, None, None, None, None
    # Конвертация в ЧБ (обработка 3 или 4 каналов)
    if len(img.shape) == 3:
        code = cv2.COLOR_RGBA2GRAY if img.shape[2] == 4 else cv2.COLOR_BGR2GRAY
        gray = cv2.cvtColor(img, code)
    else:
        gray = img

    norm = gray.astype(float)
    return (
        norm,
        np.arange(norm.shape[1]),
        np.arange(norm.shape[0]),
        np.mean(norm, axis=0),
        np.mean(norm, axis=1),
    )


def process_contrast(img, fit_result=None, base=None):
    """Контраст профиля как производная интенсивности по координате.

    Если передан результат фита (одиночный Гаусс или много гауссов),
    производную считаем от гладкого фита (она не зашумлена и отражает
    контраст именно анализируемых пиков), иначе — от сырого профиля.

    Производная укладывается в отдельные ключи `x_deriv`/`y_deriv`,
    а сам профиль остаётся в `x_raw`/`y_raw` — поэтому Plotter не заменяет
    профиль производной и не сжимает главную ось под её маленький размах.
    """
    if base is None:
        base = _get_base_profiles(img)
    if not base:
        return None
    _, x, y, x_w, y_w = base

    dx = np.gradient(x_w)
    dy = np.gradient(y_w)

    if fit_result is not None:
        t = fit_result.get("total_fit_x")
        if t is not None and np.any(t):
            dx = np.gradient(t)
        t = fit_result.get("total_fit_y")
        if t is not None and np.any(t):
            dy = np.gradient(t)

    return {
        "x": x,
        "y": y,
        "x_raw": x_w,
        "y_raw": y_w,
        "x_deriv": dx,
        "y_deriv": dy,
    }


def _local_michelson(profile, window, step):
    """Локальный нормированный контраст (Майкельсон) вдоль профиля.

    В окне `window` пикселей вокруг точки считается (max-min)/(max+min).
    Точки ставятся каждые `step` пикселей — получается набор точек,
    а не непрерывная кривая. Возвращает (позиции, значения)."""
    n = len(profile)
    half = max(1, window // 2)
    positions = []
    values = []
    for i in range(0, n, step):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        w = profile[lo:hi]
        if len(w) < 2:
            continue
        mn = float(w.min())
        mx = float(w.max())
        denom = mx + mn
        values.append((mx - mn) / denom if denom > 0 else 0.0)
        positions.append(float(i))
    return np.asarray(positions), np.asarray(values)


def estimate_contrast_params(x_profile, y_profile, min_window=3, max_window=15):
    """Подбирает параметры (window, step) локального контраста по профилям.

    Измеряет характерную ширину переходов яркости (краёв): модуль производной
    профиля, порог — доля от её максимума (робастно к уровню шума), берётся
    медианная ширина связных участков выше порога. Если выраженных краёв нет —
    окно оценивается по длине профиля. Шаг — половина окна (не пропустить
    пики). Окно ограничено [min, max]."""
    def _edge_width(profile, frac=0.35):
        g = np.abs(np.gradient(profile))
        gmax = float(np.max(g))
        if gmax <= 0:
            return None  # плоский профиль
        thresh = gmax * frac
        idx = np.flatnonzero(g >= thresh)
        if len(idx) == 0:
            return None
        splits = np.where(np.diff(idx) > 1)[0] + 1
        groups = np.split(idx, splits)
        return int(np.median([len(grp) for grp in groups]))

    widths = [
        w
        for w in (_edge_width(x_profile), _edge_width(y_profile))
        if w is not None
    ]
    if widths:
        window = int(np.median(widths))
    else:
        # Нет выраженных краёв — подбираем по длине профиля
        window = len(x_profile) // 100
    window = int(np.clip(window, min_window, max_window))
    step = max(1, window // 2)
    return window, step


def process_contrast_normalized(img, fit_result=None, window=3, step=200, base=None):
    """Нормированный локальный контраст профилей по X и по Y.

    Значения Майкельсона в [0..1]. Если есть фит (fit_result), считаем по
    гладкому фиту (без шума), иначе — по сырому профилю.
    """
    if base is None:
        base = _get_base_profiles(img)
    if not base:
        return None
    _, x, y, x_w, y_w = base

    px = x_w
    py = y_w
    if fit_result is not None:
        t = fit_result.get("total_fit_x")
        if t is not None and np.any(t):
            px = t
        t = fit_result.get("total_fit_y")
        if t is not None and np.any(t):
            py = t

    x_pos, x_val = _local_michelson(px, window, step)
    y_pos, y_val = _local_michelson(py, window, step)

    return {
        "x": x,
        "y": y,
        "x_contrast_pts": x_pos,
        "x_contrast_vals": x_val,
        "y_contrast_pts": y_pos,
        "y_contrast_vals": y_val,
    }
