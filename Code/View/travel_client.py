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
_CANDIDATE_NAMES = ("travelcore.dll", "libtravelcore.so", "libtravelcore.dylib")


def find_library(explicit_path=None):
    """Шукає shared-бібліотеку ядра: env TRAVELCORE_LIB, потім папки Controllers."""
    if explicit_path:
        return explicit_path
    env_path = os.environ.get("TRAVELCORE_LIB")
    if env_path and os.path.exists(env_path):
        return env_path
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (os.path.join(here, "..", "Controllers"), here, os.getcwd()):
        for name in _CANDIDATE_NAMES:
            candidate = os.path.join(base, name)
            if os.path.exists(candidate):
                return candidate
    raise FileNotFoundError(
        "Не знайдено зібрану бібліотеку ядра (travelcore.dll / libtravelcore.so). "
        "Спочатку виконайте збірку: Code\\build.bat або Code/build.sh. "
        "Або задайте шлях змінною середовища TRAVELCORE_LIB."
    )


class TravelClient:
    """Тонкий клієнт C API ядра TravelSystem (Controllers/c_api.cpp)."""

    def __init__(self, lib_path=None):
        self._lib = ctypes.CDLL(find_library(lib_path))
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
        lib.ts_set_tourist.restype = None
        lib.ts_set_tourist.argtypes = [
            c_void_p, c_int, c_char_p, c_double, c_int, c_int, c_double, c_char_p,
        ]
        lib.ts_get_profile.restype = c_void_p
        lib.ts_get_profile.argtypes = [c_void_p]
        lib.ts_catalog_size.restype = c_int
        lib.ts_catalog_size.argtypes = [c_void_p]
        lib.ts_routes_count.restype = c_int
        lib.ts_routes_count.argtypes = [c_void_p]
        lib.ts_filter_destinations.restype = c_void_p
        lib.ts_filter_destinations.argtypes = [c_void_p]
        lib.ts_sorted_destinations.restype = c_void_p
        lib.ts_sorted_destinations.argtypes = [c_void_p]
        lib.ts_find_shortest_path.restype = c_void_p
        lib.ts_find_shortest_path.argtypes = [c_void_p, c_int, c_int]
        lib.ts_generate_plan.restype = c_void_p
        lib.ts_generate_plan.argtypes = [c_void_p]
        lib.ts_free_string.restype = None
        lib.ts_free_string.argtypes = [c_void_p]

    # --- службовий метод: забрати рядок у C++ і звільнити його ---
    def _take_json(self, ptr):
        if not ptr:
            return None
        try:
            raw = ctypes.cast(c_void_p(ptr), c_char_p).value
            text = raw.decode("utf-8")
        finally:
            self._lib.ts_free_string(c_void_p(ptr))
        return json.loads(text)

    # --- публічні методи (відповідають use case діаграмі) ---
    def load_data(self, filename):
        """Завантажити базу даних (каталог + граф маршрутів) з JSON-файлу."""
        return self._lib.ts_load_data(self._handle, filename.encode("utf-8")) == 1

    def set_tourist(self, name, budget, is_total_budget, days, daily_time_limit, interests):
        """Створити/редагувати профіль туриста (UC1, UC4, UC5)."""
        interests_csv = ",".join(interests)
        self._lib.ts_set_tourist(
            self._handle,
            1,
            name.encode("utf-8"),
            float(budget),
            1 if is_total_budget else 0,
            int(days),
            float(daily_time_limit),
            interests_csv.encode("utf-8"),
        )

    def get_profile(self):
        return self._take_json(self._lib.ts_get_profile(self._handle))

    def catalog_size(self):
        return self._lib.ts_catalog_size(self._handle)

    def routes_count(self):
        return self._lib.ts_routes_count(self._handle)

    def filter_destinations(self):
        """Лінійний пошук/фільтрація каталогу (UC6)."""
        return self._take_json(self._lib.ts_filter_destinations(self._handle))

    def sorted_destinations(self):
        """Фільтрація + оцінка релевантності + сортування (UC6, UC7, UC9)."""
        return self._take_json(self._lib.ts_sorted_destinations(self._handle))

    def find_shortest_path(self, from_id, to_id):
        """Оптимальний маршрут алгоритмом Дейкстри (UC8)."""
        return self._take_json(self._lib.ts_find_shortest_path(self._handle, int(from_id), int(to_id)))

    def generate_plan(self):
        """Згенерувати персоналізований туристичний план (UC2)."""
        return self._take_json(self._lib.ts_generate_plan(self._handle))

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
