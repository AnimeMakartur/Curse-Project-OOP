"""Клієнт міжмовної взаємодії: обгортка ctypes над C++ ядром (travelcore).

Шар представлення (Python) викликає методи C++ ядра як прості транзакції
через динамічну бібліотеку. Усі результати C++ повертає у вигляді JSON-рядків,
які тут розбираються готовим парсером (json.loads). JSON-файл бази даних теж
читається готовим парсером Python — стандартним модулем json
(див. db_loader.loadDatabase); C++ ядро JSON не парсить.

Тип смуги (LaneType) передається у C++ як int; рядкові ключі, українські назви
та дефолтні параметри смуг — у модулі lane_types.
"""

import ctypes
import json
import os
import sys
from ctypes import c_char_p, c_double, c_int, c_void_p

from db_loader import loadDatabase, normalizeLane
from lane_types import enrich_lane, lane_defaults, lane_type_to_int

# Можливі місця розташування зібраної бібліотеки (за пріоритетом)
_CandidateNames = ("travelcore.dll", "libtravelcore.so", "libtravelcore.dylib")


def appBaseDir():
    """Базова папка застосунку.

    У зібраному PyInstaller-exe (sys.frozen) __file__ модулів вказує на тимчасову
    папку _MEIPASS, тому базою вважаємо папку самого exe (sys.executable) — відносно
    неї у папці релізу лежать ../Controllers і ../DataBase. У режимі запуску з сирців
    (python app.py) — папка цього файлу (Code/View).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def findLibrary(explicitPath=None):
    """Шукає shared-бібліотеку ядра: env TRAVELCORE_LIB, потім папки Controllers."""
    if explicitPath:
        return explicitPath
    envPath = os.environ.get("TRAVELCORE_LIB")
    if envPath and os.path.exists(envPath):
        return envPath
    here = appBaseDir()
    bases = [os.path.join(here, "..", "Controllers"), here, os.getcwd()]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bases.insert(1, meipass)  # dll, запакована всередину exe через --add-binary
    for base in bases:
        for name in _CandidateNames:
            candidate = os.path.join(base, name)
            if os.path.exists(candidate):
                return candidate
    raise FileNotFoundError(
        "Core library not found (travelcore.dll / libtravelcore.so). "
        "Build it first: Code\\build.bat or Code/build.sh. "
        "Or set the path via the TRAVELCORE_LIB environment variable."
    )


def _enrichLanes(obj):
    """Рекурсивно збагатити всі lane-об'єкти в структурі рядковими/укр. полями."""
    if isinstance(obj, dict):
        if "type" in obj and isinstance(obj.get("type"), int) and "routeName" in obj:
            enrich_lane(obj)
        for v in obj.values():
            _enrichLanes(v)
    elif isinstance(obj, list):
        for item in obj:
            _enrichLanes(item)
    return obj


def _fmtPlanSummary(plan):
    """Текстовий підсумок плану (колишній TravelPlan::exportPlanSummary у C++)."""
    lines = [
        f"=== Personalized travel plan for {plan.get('tourist', '')} "
        f"(city id={plan.get('targetCityId', -1)}) ===",
        f"Total: cost {plan.get('totalCost', 0):g} EUR "
        f"(remaining budget {plan.get('remainingBudget', 0):g} EUR), "
        f"time on site {plan.get('totalVisitTime', 0):g} h, "
        f"travel time {plan.get('totalTravelTime', 0):g} h, "
        f"total {plan.get('totalDuration', 0):g} h.",
        "",
    ]
    for day in plan.get("days", []):
        lines.append(f"Day {day['day']}:")
        items = day.get("items", [])
        if not items:
            lines.append("  (free day)")
            lines.append("")
            continue
        for i, item in enumerate(items):
            for t in item.get("transfers", []):
                lane = t.get("lane", {})
                desc = lane.get("description", lane.get("type", ""))
                lines.append(
                    f"  -> transfer {t.get('fromName', t['fromId'])} -> "
                    f"{t.get('toName', t['toId'])}: {t['distanceKm']:g} km, "
                    f"{t['timeHours']:g} h, {t['cost']:g} EUR — {desc}"
                )
            dest = item.get("destination")
            if dest:
                lines.append(
                    f"  {i + 1}. {dest['name']} ({dest['type']}, {dest['cost']:g} EUR, "
                    f"{dest['visitDuration']:g} h, rating {dest['rating']:g})"
                )
        lines.append("")
    return "\n".join(lines)


class TravelClient:
    """Тонкий клієнт C API ядра TravelSystem (Controllers/Src/c_api.cpp)."""

    def __init__(self, libPath=None):
        libPath = findLibrary(libPath)
        if os.name == "nt" and hasattr(os, "add_dll_directory"):
            # Папка з самою dll потрапляє у пошук залежностей LoadLibrary:
            # якщо поруч із travelcore.dll лежать її залежності — знайдуться.
            os.add_dll_directory(os.path.dirname(os.path.abspath(libPath)))
        self._lib = ctypes.CDLL(libPath)
        self._handle = None
        self._bind()
        self._handle = self._lib.ts_create()
        self._namesById = {}  # id вершини графа -> назва об'єкта (для маршрутів замість ID)

    # --- налаштування сигнатур C API ---
    def _bind(self):
        lib = self._lib
        lib.ts_create.restype = c_void_p
        lib.ts_create.argtypes = []
        lib.ts_destroy.restype = None
        lib.ts_destroy.argtypes = [c_void_p]
        lib.ts_clear_data.restype = None
        lib.ts_clear_data.argtypes = [c_void_p]
        lib.ts_add_city.restype = None
        lib.ts_add_city.argtypes = [c_void_p, c_int, c_char_p, c_char_p, c_char_p]
        lib.ts_add_attraction.restype = None
        lib.ts_add_attraction.argtypes = [
            c_void_p,
            c_int,
            c_int,
            c_char_p,
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            c_char_p,
            c_int,
            c_char_p,
            c_int,
        ]
        lib.ts_add_museum.restype = None
        lib.ts_add_museum.argtypes = [
            c_void_p,
            c_int,
            c_int,
            c_char_p,
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            c_char_p,
            c_int,
            c_int,
            c_char_p,
        ]
        lib.ts_add_route.restype = c_int
        lib.ts_add_route.argtypes = [c_void_p, c_int, c_int, c_int, c_double]
        # laneType — int (enum LaneType), а не рядок
        lib.ts_add_lane.restype = None
        lib.ts_add_lane.argtypes = [
            c_void_p,
            c_int,
            c_int,
            c_char_p,
            c_double,
            c_double,
            c_double,
            c_double,
        ]
        lib.ts_cities_count.restype = c_int
        lib.ts_cities_count.argtypes = [c_void_p]
        lib.ts_get_cities.restype = c_void_p
        lib.ts_get_cities.argtypes = [c_void_p]
        lib.ts_set_tourist.restype = None
        lib.ts_set_tourist.argtypes = [
            c_void_p,
            c_int,
            c_char_p,
            c_double,
            c_int,
            c_int,
            c_double,
            c_char_p,
            c_int,
            c_int,
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
        """Завантажити базу даних (міста + каталог + графи маршрутів) з JSON-файлу.

        JSON-файл читає готовий парсер Python (стандартний модуль json у
        db_loader); у C++ ядро сутності передаються через ts_add_* — C++ JSON
        не парсить.
        """
        try:
            data = loadDatabase(filename)
        except FileNotFoundError:
            raise RuntimeError(f"Failed to open database file: {filename}") from None
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON parse error in {filename}: {e}") from None
        except ValueError as e:
            raise RuntimeError(str(e)) from None

        lib = self._lib
        h = self._handle
        lib.ts_clear_data(h)
        for c in data["cities"]:
            lib.ts_add_city(
                h,
                int(c.get("id", 0)),
                str(c.get("name", "")).encode("utf-8"),
                str(c.get("region", "")).encode("utf-8"),
                str(c.get("description", "")).encode("utf-8"),
            )
        for d in data["destinations"]:
            tagsCsv = ",".join(str(t) for t in d.get("tags", [])).encode("utf-8")
            common = (
                h,
                int(d.get("id", 0)),
                int(d.get("cityId", 0)),
                str(d.get("name", "")).encode("utf-8"),
                float(d.get("cost", 0.0)),
                float(d.get("rating", 0.0)),
                float(d.get("visitDuration", 0.0)),
                float(d.get("openHour", 9.0)),
                float(d.get("closeHour", 18.0)),
                tagsCsv,
            )
            if d.get("type") == "museum":
                lib.ts_add_museum(
                    *common,
                    int(d.get("exhibitsCount", 0)),
                    1 if d.get("hasAudioGuide") else 0,
                    str(d.get("expositionTheme", "")).encode("utf-8"),
                )
            else:  # attraction / hotel — як пам'ятка
                lib.ts_add_attraction(
                    *common,
                    1 if d.get("isOutdoor") else 0,
                    str(d.get("architecturalStyle", "")).encode("utf-8"),
                    1 if d.get("isSeasonal") else 0,
                )
        for r in data["routes"]:
            routeIndex = lib.ts_add_route(
                h,
                int(r.get("cityId", 0)),
                int(r.get("fromId", 0)),
                int(r.get("toId", 0)),
                float(r.get("distanceKm", 0.0)),
            )
            for lane in r.get("lanes", []):
                self._addLane(routeIndex, lane)
        self._namesById = {d["id"]: d.get("name", "") for d in self.getCatalog(-1)}
        return True

    def _addLane(self, routeIndex, lane):
        """Додати одну смугу/лінію до ребра графа.

        ``lane`` — рядок ("sidewalk") або dict із підмножиною полів; відсутні
        числові поля добираються з дефолтів типу смуги на боці Python
        (lane_types.lane_defaults).
        """
        laneType = lane if isinstance(lane, str) else str(lane.get("type", "sidewalk"))
        base, mult, cost, wait = lane_defaults(laneType)
        lane = normalizeLane(lane, (mult, base, cost, wait))
        self._lib.ts_add_lane(
            self._handle,
            int(routeIndex),
            lane_type_to_int(lane["type"]),
            lane["routeName"].encode("utf-8"),
            lane["speedMultiplier"],
            lane["baseSpeedKmh"],
            lane["cost"],
            lane["waitTimeHours"],
        )

    def destinationName(self, destId):
        """Назва об'єкта за id вершини графа (fallback — 'id=N', якщо об'єкта немає в каталозі)."""
        name = self._namesById.get(int(destId))
        return name if name else f"id={destId}"

    def _enrichPath(self, steps):
        """Додає до кожного кроку маршруту назви вершин (fromName/toName) замість голих ID."""
        for s in steps:
            s["fromName"] = self.destinationName(s["fromId"])
            s["toName"] = self.destinationName(s["toId"])
        return steps

    def getCities(self):
        """Список міст/агломерацій із завантаженої бази: [{id, name, region, description}]."""
        return self._takeJson(self._lib.ts_get_cities(self._handle)) or []

    def citiesCount(self):
        return self._lib.ts_cities_count(self._handle)

    def setTourist(
        self, name, budget, isTotalBudget, days, dailyTimeLimit, interests, cityId=-1, hasCar=False
    ):
        """Створити/редагувати профіль туриста (UC1, UC4, UC5) із обраним містом cityId.

        hasCar — чи є в туриста власна машина: тоді car_lane доступна в Дейкстрі,
        а шлях на машині згортається в один прямий перегін між об'єктами.
        """
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
            1 if hasCar else 0,
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
        """Ребра транспортного графа міста зі списком смуг/ліній (lane збагачені рядковими полями)."""
        routes = self._takeJson(self._lib.ts_get_routes(self._handle, int(cityId))) or []
        return _enrichLanes(routes)

    def filterDestinations(self):
        """Лінійний пошук/фільтрація каталогу обраного міста (UC6)."""
        return self._takeJson(self._lib.ts_filter_destinations(self._handle)) or []

    def sortedDestinations(self):
        """Фільтрація + оцінка релевантності + сортування (UC6, UC7, UC9)."""
        return self._takeJson(self._lib.ts_sorted_destinations(self._handle)) or []

    def findShortestPath(self, fromId, toId, budget=None):
        """Оптимальний маршрут алгоритмом Дейкстри (UC8) з деталізацією ліній транспорту.

        Кожен крок додатково містить fromName/toName — назви об'єктів замість ID вершин,
        а lane збагачений рядковими/українськими полями (type, typeUkr, transportUkr, description).
        """
        if budget is None:
            steps = (
                self._takeJson(
                    self._lib.ts_find_shortest_path(self._handle, int(fromId), int(toId))
                )
                or []
            )
        else:
            steps = (
                self._takeJson(
                    self._lib.ts_find_shortest_path_budget(
                        self._handle, int(fromId), int(toId), float(budget)
                    )
                )
                or []
            )
        _enrichLanes(steps)
        return self._enrichPath(steps)

    def generatePlan(self):
        """Згенерувати персоналізований туристичний план (UC2).

        Трансфери всередині плану збагачені назвами об'єктів (fromName/toName)
        та рядковими полями смуг; текстовий summary формується тут, у Python.
        """
        plan = self._takeJson(self._lib.ts_generate_plan(self._handle))
        if plan:
            _enrichLanes(plan)
            for day in plan.get("days", []):
                for item in day.get("items", []):
                    self._enrichPath(item.get("transfers", []))
            plan["summary"] = _fmtPlanSummary(plan)
        return plan

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
