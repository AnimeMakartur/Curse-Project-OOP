"""Завантаження локальної бази даних travel_db.json готовим парсером Python.

Це єдине місце, де програма парсить JSON: стандартний модуль ``json``
(``json.load``) із стандартної бібліотеки. Власного C++ JSON-парсера в проєкті
більше немає (JsonParser.h видалено) — C++ ядро отримує вже розібрані сутності
через C API (див. ``travel_client.TravelClient.loadData``).

Формат файла описано у ``Code/DataBase/schema.md``:
``{"cities": [...], "destinations": [...], "routes": [...]}``.
"""

import json


def loadDatabase(path):
    """Прочитати JSON-файл бази даних готовим парсером stdlib і повернути dict.

    Повертає ``{"cities": [...], "destinations": [...], "routes": [...]}``
    (відсутні секції вважаються порожніми списками).

    Помилки:
      FileNotFoundError — файла немає;
      json.JSONDecodeError — файл не є коректним JSON;
      ValueError — корінь JSON не є об'єктом.
    """
    with open(path, "r", encoding="utf-8") as f:
        root = json.load(f)  # готовий парсер стандартної бібліотеки
    if not isinstance(root, dict):
        raise ValueError(f"Корінь JSON бази має бути об'єктом: {path}")
    return {
        "cities": root.get("cities") or [],
        "destinations": root.get("destinations") or [],
        "routes": root.get("routes") or [],
    }


def normalizeLane(lane, defaults):
    """Нормалізувати запис смуги/лінії з JSON до повного dict.

    ``lane`` — або рядок ("sidewalk"), або об'єкт із підмножиною полів
    ``type/routeName/speedMultiplier/baseSpeedKmh/cost/waitTimeHours``.
    ``defaults`` — кортеж (speedMultiplier, baseSpeedKmh, cost, waitTimeHours)
    дефолтів типу смуги з Python-довідника lane_types; відсутні поля беруться з нього.
    """
    if isinstance(lane, str):
        lane = {"type": lane}
    if not isinstance(lane, dict):
        lane = {"type": "sidewalk"}
    mult, speed, cost, wait = defaults
    return {
        "type": str(lane.get("type", "sidewalk")),
        "routeName": str(lane.get("routeName", lane.get("name", ""))),
        "speedMultiplier": float(lane.get("speedMultiplier", mult)),
        "baseSpeedKmh": float(lane.get("baseSpeedKmh", speed)),
        "cost": float(lane.get("cost", cost)),
        "waitTimeHours": float(lane.get("waitTimeHours", wait)),
    }
