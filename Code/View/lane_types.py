"""Довідник типів смуг/ліній транспорту (перенесено з C++ Lane.cpp).

C++ ядро оперує типом смуги як int (enum LaneType), а всі рядкові
представлення, українські назви та дефолтні параметри — тут, у Python.
Порядок записів відповідає enum class LaneType у Lane.h.
"""

# Індекс = int-значення enum LaneType у C++ (має збігатися з Lane.h)
LANE_KEYS = [
    "sidewalk",
    "bike_lane",
    "car_lane",
    "bus_lane",
    "metrobus",
    "tram_line",
    "suburban_rail",
    "railway",
]

# Коротка назва (typeUkr)
LANE_NAMES_UKR = [
    "sidewalk",
    "bike lane",
    "car lane",
    "dedicated bus lane",
    "metrobus line",
    "express tram",
    "suburban train",
    "city railway",
]

# Опис виду транспорту (transportUkr)
LANE_TRANSPORT_UKR = [
    "On foot (sidewalk)",
    "Bicycle (bike lane)",
    "Car (general lane)",
    "Bus (dedicated bus lane)",
    "Metrobus (BRT)",
    "Express tram",
    "Suburban train",
    "City railway",
]

# Дефолтні параметри: (baseSpeedKmh, speedMultiplier, cost, waitTimeHours)
LANE_DEFAULTS = [
    (5.0, 1.0, 0.0, 0.0),      # sidewalk
    (15.0, 1.0, 0.0, 0.0),     # bike_lane
    (30.0, 1.0, 0.0, 0.0),     # car_lane
    (30.0, 1.3, 0.30, 0.15),   # bus_lane
    (40.0, 1.5, 0.40, 0.10),   # metrobus
    (35.0, 1.6, 0.30, 0.12),   # tram_line
    (70.0, 1.4, 0.60, 0.25),   # suburban_rail
    (90.0, 1.6, 0.90, 0.30),   # railway
]

# Альтернативні рядкові ключі (українські синоніми) -> canonical key
LANE_ALIASES = {
    "тротуар": "sidewalk",
    "велодоріжка": "bike_lane",
    "велосипедна доріжка": "bike_lane",
    "автомобільна смуга": "car_lane",
    "автомобільна дорога": "car_lane",
    "автобусна смуга": "bus_lane",
    "виділена автобусна смуга": "bus_lane",
    "метробус": "metrobus",
    "brt": "metrobus",
    "лінія метробуса": "metrobus",
    "трамвайна лінія": "tram_line",
    "швидкісний трамвай": "tram_line",
    "відокремлена лінія трамвая": "tram_line",
    "приміська електричка": "suburban_rail",
    "електричка": "suburban_rail",
    "залізниця": "railway",
    "залізнична колія": "railway",
    "міська залізниця": "railway",
}


def lane_type_to_int(key):
    """Canonical рядковий ключ (або синонім) -> int enum для C++ API."""
    key = LANE_ALIASES.get(key, key)
    try:
        return LANE_KEYS.index(key)
    except ValueError:
        return 0  # sidewalk за замовчуванням


def lane_type_from_int(value):
    """int enum з C++ -> canonical рядковий ключ."""
    idx = int(value)
    if 0 <= idx < len(LANE_KEYS):
        return LANE_KEYS[idx]
    return "sidewalk"


def lane_type_ukr(value):
    idx = int(value)
    return LANE_NAMES_UKR[idx] if 0 <= idx < len(LANE_NAMES_UKR) else "sidewalk"


def lane_transport_ukr(value):
    idx = int(value)
    return LANE_TRANSPORT_UKR[idx] if 0 <= idx < len(LANE_TRANSPORT_UKR) else "On foot (sidewalk)"


def lane_defaults(key):
    """Дефолтні параметри смуги: (baseSpeedKmh, speedMultiplier, cost, waitTimeHours)."""
    idx = lane_type_to_int(key)
    return LANE_DEFAULTS[idx]


def lane_describe(lane):
    """Людиночитний опис смуги: «Вид транспорту „Назва маршруту“»."""
    transport = lane_transport_ukr(lane["typeInt"])
    name = lane.get("routeName", "")
    return f"{transport} «{name}»" if name else transport


def enrich_lane(lane):
    """Додати до dict смуги (що прийшов з C++ JSON) рядкові/українські поля."""
    t = lane.get("type", 0)
    if isinstance(t, str):
        t = lane_type_to_int(t)
    lane["typeInt"] = t
    lane["type"] = lane_type_from_int(t)
    lane["typeUkr"] = lane_type_ukr(t)
    lane["transportUkr"] = lane_transport_ukr(t)
    lane["description"] = lane_describe(lane)
    return lane
