"""Клієнт міжмовної взаємодії: обгортка ctypes над C++ ядром (travelcore).

Шар представлення (Python) викликає методи C++ ядра як прості транзакції
через динамічну бібліотеку. Усі результати C++ повертає у вигляді JSON-рядків,
які тут перетворюються на Python-об'єкти.
"""

import ctypes
import json
import os
from ctypes import c_char_p, c_double, c_int, c_void_p

# Можливі місця розташування зібраної бібліотеки (за пріоритетом)
_CandidateNames = ("travelcore.dll", "libtravelcore.so", "libtravelcore.dylib")


def findLibrary(explicitPath=None):
    """Шукає shared-бібліотеку ядра: env TRAVELCORE_LIB, потім папки Controllers."""
    if explicitPath:
        return explicitPath
    envPath = os.environ.get("TRAVELCORE_LIB")
    if envPath and os.path.exists(envPath):
        return envPath
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (os.path.join(here, "..", "Controllers"), here, os.getcwd()):
        for name in _CandidateNames:
            candidate = os.path.join(base, name)
            if os.path.exists(candidate):
                return candidate
    raise FileNotFoundError(
        "Core library not found (travelcore.dll / libtravelcore.so). "
        "Build it first: Code\\build.bat or Code/build.sh. "
        "Or set the path via the TRAVELCORE_LIB environment variable."
    )


class TravelClient:
    """Тонкий клієнт C API ядра TravelSystem (Controllers/c_api.cpp)."""

    def __init__(self, libPath=None):
        self._lib = ctypes.CDLL(findLibrary(libPath))
        self._handle = None
        self._bind()
        self._handle = self._lib.ts_create()

    # --- налаштування сигнатур C API ---
    def _bind(self):
        lib = self._lib
        lib.ts_create.restype = c_void_p
        lib.ts_create.argtypes = []
        lib.ts_destroy.restype = None
        lib.ts_destroy.argtypes = [c_void_p]
        lib.ts_load_data.restype = c_int
        lib.ts_load_data.argtypes = [c_void_p, c_char_p]
        lib.ts_last_error.restype = c_char_p
        lib.ts_last_error.argtypes = []
        lib.ts_cities_count.restype = c_int
        lib.ts_cities_count.argtypes = [c_void_p]
        lib.ts_get_cities.restype = c_void_p
        lib.ts_get_cities.argtypes = [c_void_p]
        lib.ts_set_tourist.restype = None
        lib.ts_set_tourist.argtypes = [
            c_void_p, c_int, c_char_p, c_double, c_int, c_int, c_double, c_char_p, c_int,
        ]
        lib.ts_set_target_city.restype = None
        lib.ts_set_target_city.argtypes = [c_void_p, c_int]
        lib.ts_get_profile.restype = c_void_p
        lib.ts_get_profile.argtypes = [c_void_p]
        lib.ts_catalog_size.restype = c_int
        lib.ts_catalog_size.argtypes = [c_void_p]
        lib.ts_routes_count.restype = c_int
        lib.ts_routes_count.argtypes = [c_void_p]
        lib.ts_catalog.restype = c_void_p
        lib.ts_catalog.argtypes = [c_void_p, c_int]
        lib.ts_get_routes.restype = c_void_p
        lib.ts_get_routes.argtypes = [c_void_p, c_int]
        lib.ts_filter_destinations.restype = c_void_p
        lib.ts_filter_destinations.argtypes = [c_void_p]
        lib.ts_sorted_destinations.restype = c_void_p
        lib.ts_sorted_destinations.argtypes = [c_void_p]
        lib.ts_find_shortest_path.restype = c_void_p
        lib.ts_find_shortest_path.argtypes = [c_void_p, c_int, c_int]
        lib.ts_find_shortest_path_budget.restype = c_void_p
        lib.ts_find_shortest_path_budget.argtypes = [c_void_p, c_int, c_int, c_double]
        lib.ts_generate_plan.restype = c_void_p
        lib.ts_generate_plan.argtypes = [c_void_p]
        lib.ts_free_string.restype = None
        lib.ts_free_string.argtypes = [c_void_p]

    # --- службовий метод: забрати рядок у C++ і звільнити його ---
    def _takeJson(self, ptr):
        if not ptr:
            return None
        try:
            raw = ctypes.cast(c_void_p(ptr), c_char_p).value
            text = raw.decode("utf-8")
        finally:
            self._lib.ts_free_string(c_void_p(ptr))
        return json.loads(text)

    # --- публічні методи (відповідають use case діаграмі) ---
    def loadData(self, filename):
        """Завантажити базу даних (міста + каталог + графи маршрутів) з JSON-файлу."""
        ok = self._lib.ts_load_data(self._handle, filename.encode("utf-8")) == 1
        if not ok:
            err = self._lib.ts_last_error()
            raise RuntimeError(
                "Failed to load the database: %s (%s)" % (filename, err.decode("utf-8") if err else "?")
            )
        return True

    def getCities(self):
        """Список міст/агломерацій із завантаженої бази: [{id, name, region, description}]."""
        return self._takeJson(self._lib.ts_get_cities(self._handle)) or []

    def citiesCount(self):
        return self._lib.ts_cities_count(self._handle)

    def setTourist(self, name, budget, isTotalBudget, days, dailyTimeLimit, interests,
                   cityId=-1):
        """Створити/редагувати профіль туриста (UC1, UC4, UC5) із обраним містом cityId."""
        interestsCsv = ",".join(interests)
        self._lib.ts_set_tourist(
            self._handle,
            1,
            name.encode("utf-8"),
            float(budget),
            1 if isTotalBudget else 0,
            int(days),
            float(dailyTimeLimit),
            interestsCsv.encode("utf-8"),
            int(cityId),
        )

    def setTargetCity(self, cityId):
        """Змінити обране місто/агломерацію у поточному профілі туриста."""
        self._lib.ts_set_target_city(self._handle, int(cityId))

    def getProfile(self):
        return self._takeJson(self._lib.ts_get_profile(self._handle))

    def catalogSize(self):
        return self._lib.ts_catalog_size(self._handle)

    def routesCount(self):
        return self._lib.ts_routes_count(self._handle)

    def getCatalog(self, cityId=-1):
        """Повний каталог об'єктів міста (cityId=-1 — усі міста) для GUI-таблиці."""
        return self._takeJson(self._lib.ts_catalog(self._handle, int(cityId))) or []

    def getRoutes(self, cityId=-1):
        """Ребра транспортного графа міста зі списком смуг/ліній."""
        return self._takeJson(self._lib.ts_get_routes(self._handle, int(cityId))) or []

    def filterDestinations(self):
        """Лінійний пошук/фільтрація каталогу обраного міста (UC6)."""
        return self._takeJson(self._lib.ts_filter_destinations(self._handle)) or []

    def sortedDestinations(self):
        """Фільтрація + оцінка релевантності + сортування (UC6, UC7, UC9)."""
        return self._takeJson(self._lib.ts_sorted_destinations(self._handle)) or []

    def findShortestPath(self, fromId, toId, budget=None):
        """Оптимальний маршрут алгоритмом Дейкстри (UC8) з деталізацією ліній транспорту."""
        if budget is None:
            return self._takeJson(
                self._lib.ts_find_shortest_path(self._handle, int(fromId), int(toId))
            ) or []
        return self._takeJson(
            self._lib.ts_find_shortest_path_budget(
                self._handle, int(fromId), int(toId), float(budget)
            )
        ) or []

    def generatePlan(self):
        """Згенерувати персоналізований туристичний план (UC2)."""
        return self._takeJson(self._lib.ts_generate_plan(self._handle))

    def close(self):
        if self._handle is not None:
            self._lib.ts_destroy(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
