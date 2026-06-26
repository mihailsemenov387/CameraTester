import cv2
import numpy as np
from scipy.optimize import curve_fit

WINDOW = 1000
THRESH = 0.3


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
    except Exception as e:
        # Если фиттинг не сошелся
        return (0, 0, 0, 1, 0)


def process(img):
    if img is None:
        return None

    # !!! ШАГ 1: ПЕРЕВОДИМ В ЧЕРНО-БЕЛЫЙ !!!
    # Если картинка 3-канальная (BGR/RGB), берем яркость
    if len(img.shape) == 3:
        # Проверяем, сколько каналов (иногда бывает 4 с альфа-каналом)
        if img.shape[2] == 4:
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        else:
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        img_gray = img

    img_norm = img_gray.astype(float)

    # Фон и фильтрация
    background = np.mean(img_norm[0:20, 0:20])
    img_norm = img_norm - background
    thresh = np.max(img_norm) * THRESH
    img_norm[img_norm < thresh] = 0

    # Профили теперь точно 1D
    x_w = np.mean(img_norm, axis=0)
    y_w = np.mean(img_norm, axis=1)

    x = np.arange(len(x_w))
    y = np.arange(len(y_w))

    # Фиттинг
    res_x = fit_gaussian(x, x_w)  # (sigma_est, A, mu, sigma, B)
    res_y = fit_gaussian(y, y_w)

    X_gauss = gauss(x, *res_x[1:])
    Y_gauss = gauss(y, *res_y[1:])

    # Собираем данные для графиков и UI
    data = {
        "x": x,
        "y": y,
        "x_w": x_w,
        "y_w": y_w,
        "X_gauss": X_gauss,
        "Y_gauss": Y_gauss,
        "mu_x": res_x[2],
        "mu_y": res_y[2],
        "sigma_x": res_x[3],
        "sigma_y": res_y[3],
        "amp_x": res_x[1],
        "amp_y": res_y[1],
    }

    return data
