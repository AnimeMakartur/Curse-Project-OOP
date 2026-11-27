# TravelSystem — програмне забезпечення для автоматичного персоналізованого підбору туристичного плану

Курсовий проєкт з дисципліни «Об'єктно-орієнтоване програмування».
Автономна інформаційно-аналітична система (CARS): будує персоналізований
туристичний план **в межах обраного міста/агломерації** з урахуванням бюджету,
часу, годин роботи об'єктів, інтересів туриста та **мультимодальної транспортної
мережі** (смуги руху й лінії громадського транспорту на кожній ділянці дороги).

## Архітектура (три шари)

| Шар                                | Мова                 | Папка                                                                                | Призначення                                                                                                                   |
| ---------------------------------- | -------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Представлення (GUI)                | Python 3 + **PyQt6** | `Code/View`, точка входу `Code/Main.py`                                              | Віконний інтерфейс: вибір міста, профіль туриста, каталог (QTableWidget), план по днях, метрики; консольний режим `--console` |
| Бізнес-логіка / обчислювальне ядро | **C++17**            | `Code/Controllers`, `Code/Models` (підпапки `Include/` для `.h` і `Src/` для `.cpp`) | Моделі предметної області, алгоритми (лінійний пошук, сортування, Дейкстра з чергою з пріоритетом), фасад `TravelSystem`      |
| Дані та міжмовна взаємодія         | JSON + C API         | `Code/DataBase`, `Controllers/Src/c_api.cpp`                                         | Локальна база `travel_db.json` (міста + об'єкти + графи), `extern "C"` API для ctypes                                          |

Міжмовна взаємодія: Python GUI викликає методи C++ ядра через динамічну
бібліотеку (`travelcore.dll` / `libtravelcore.so`) засобами `ctypes`
(`Code/View/travel_client.py`). Усі результати C++ повертає у вигляді JSON-рядків.

**JSON парсить готовий парсер Python** — стандартний модуль `json`
(`Code/View/db_loader.py`, `json.load` / `json.loads`). Власного C++ JSON-парсера
в проєкті немає: C++ ядро отримує вже розібрані сутності через C API
(`ts_add_city` / `ts_add_attraction` / `ts_add_museum` / `ts_add_route` / `ts_add_lane`).

Потік даних: `Main.py → PyQt6 GUI → ctypes → C API (c_api.cpp) → TravelSystem → Algorithms`;
база: `travel_db.json → json.load (Python) → ts_add_* → C++ ядро`.

## Модель даних: міста та мультимодальна транспортна мережа

- **Міста/агломерації** (`cities`): кожне місто має унікальний `id`, `name`,
  `region`, `description`. Об'єкти (`destinations.cityId`) та ребра графів
  (`routes.cityId`) прив'язані до міста. `Tourist.targetCityId` задає місто
  подорожі — фільтрація, Дейкстра та план працюють **лише в його межах**.
- **Ребро графа** (`Route`): ділянка `(u, v)` довжиною `distanceKm` із набором
  смуг/ліній `lanes`: `sidewalk`, `bike_lane`, `car_lane`, `bus_lane` (виділена
  автобусна смуга), `metrobus` (BRT), `tram_line` (швидкісний трамвай),
  `suburban_rail` (приміська електричка), `railway` (міська залізниця).
  Для кожної лінії задано `routeName` (напр. «Трамвай №8»), `speedMultiplier`,
  `baseSpeedKmh`, `cost`, `waitTimeHours`.
- **Вибір лінії у Дейкстри**: вага ребра — мінімальний час серед ліній, що
  вписуються в залишок бюджету:
  `t(u,v) = min_l ( distanceKm / (v_base·k_speed(l)) + t_wait(l) )`.
  План повертає деталізовані кроки (`PathStep`): якою саме лінією/смутою
  здійснено перехід, скільки часу це зайняло та яка вартість проїзду.

## Структура проєкту

```
├── Dockerfile / docker-compose.yml / requirements.txt   # розгортання в один клік
├── README.MD                                            # цей файл
└── Code/
    ├── Main.py                  # головна точка входу: python Main.py (GUI/--console); з нього ж збирається .exe
    ├── Models/                  # класи предметної області (ООП)
    │   ├── Include/             #   заголовки (.h)
    │   │   ├── City.h           #   місто/агломерація (id, назва, регіон, опис)
    │   │   ├── Tourist.h        #   турист: targetCityId, бюджет (денний/загальний), дні, інтереси
    │   │   ├── TouristDestination.h # абстрактний базовий клас об'єкта (cityId, protected-поля)
    │   │   ├── Attraction.h     #   пам'ятка (успадкування, поліморфізм)
    │   │   ├── Museum.h         #   музей (успадкування, поліморфізм)
    │   │   ├── Lane.h           #   смуга/лінія: тип, маршрут, k_speed, v_base, cost, waitTime
    │   │   ├── Route.h          #   ребро графа: cityId, distanceKm, набір lanes, вибір найкращої лінії
    │   │   ├── PathStep.h       #   крок маршруту: ребро + обрана лінія + час + вартість
    │   │   └── TravelPlan.h     #   план по днях (DayItem: об'єкт + transfers), метрики, експорт
    │   └── Src/                 #   реалізація (.cpp тих самих класів)
    ├── Controllers/             # керуюче ядро
    │   ├── Include/             #   заголовки (.h): Algorithms.h, TravelSystem.h
    │   └── Src/                 #   реалізація (.cpp): Algorithms.cpp, TravelSystem.cpp,
    │                            #   c_api.cpp — extern "C" API для ctypes (ts_get_cities, ts_set_tourist, ts_generate_plan, ...)
    ├── DataBase/
    │   ├── travel_db.json       #   локальна база (міста + об'єкти + графи); читається Python-ом (модуль json)
    │   └── schema.md            #   опис формату БД і приклад записів
    ├── View/
    │   ├── db_loader.py         #   JSON-парсер бази: готовий парсер stdlib (json.load)
    │   ├── travel_client.py     #   ctypes-обгортка над C API (loadData передає дані через ts_add_*)
    │   ├── main_window.py       #   головне вікно PyQt6 (каталог, план, метрики, шлях)
    │   └── app.py               #   логіка запуску: GUI (PyQt6) або --console (з Main.py)
    ├── Tests/
    │   ├── smoke_test.cpp       #   консольний тест ядра без GUI і без JSON (демо-дані в коді)
    │   └── sample_db.json       #   демо-база з двома містами для Python-режиму --console
    ├── build.bat                #   збірка DLL (Windows: g++ / clang++ / MSVC cl), прапорець --tests
    ├── run.bat                  #   запуск програми: python Main.py (GUI/--console, --build)
    ├── test.bat                 #   запуск smoke-тестів ядра
    └── build.sh                 #   збірка .so (Linux/macOS: g++ / clang++), прапорець --tests
```

## Класи (відповідно до діаграми класів, розширено)

- `City` — місто/агломерація: `id`, `name`, `region`, `description`.
- `Tourist` — `targetCityId`, `getDailyBudget()` (формула 1.7), `getTotalBudget()` (1.8), `getInterests()`, `updateProfile(...)`.
- `TravelSystem` — фасад: наповнення даними через `clearData`/`addCity`/`addDestination`/`addRoute`/`addLane`
  (JSON читає Python), `getCities`, `setTouristProfile`,
  `filterDestinations` (лінійний пошук **за targetCityId**), `sortDestinations` (релевантність, 1.4),
  `generatePersonalizedPlan`, `findShortestPath` (Дейкстра з бюджетом і вибором лінії).
- `TouristDestination` (abstract) — `cityId`, `isOpen`, поліморфні `calculateRelevance`, `getDetails`, `getType`.
- `Attraction`, `Museum` — похідні класи.
- `Lane` — смуга/лінія: `type`, `routeName`, `speedMultiplier`, `baseSpeedKmh`, `cost`, `waitTimeHours`,
  `travelTimeHours(distanceKm)`, `describe()`.
- `Route` — ребро графа: `cityId`, `fromId/toId`, `distanceKm`, `lanes`,
  `chooseBestLane(budget)` — оптимальна лінія з мінімальним часом у межах бюджету.
- `PathStep` — крок маршруту: `route` + `lane` + `timeHours` + `cost`.
- `TravelPlan` — `addDayStep(day, dest, transfers)`, `calculateTotalMetrics`, `exportPlanSummary`.

## Вимоги

- **Docker** (рекомендовано): Docker Engine + Docker Compose v2.
- **Локально**: Python 3.10+ із `PyQt6` (`pip install -r requirements.txt`) та компілятор
  C++17: Windows — MinGW/MSYS2 (`g++`), LLVM (`clang++`) або MSVC Build Tools (`cl`);
  Linux/macOS — `g++` або `clang++`.

## Розгортання та запуск

### 2. Локальна збірка та запуск

Windows (з кореня проєкту):

```bat
Code\build.bat            REM або Code\build.bat --tests — ще й smoke-тест
Code\run.bat              REM або вручну: cd Code && python Main.py   (GUI, потрібен pip install PyQt6)
```

Linux/macOS:

```bash
cd Code && chmod +x build.sh && ./build.sh        # або ./build.sh --tests
python Main.py                                     # GUI
```

→ з'явиться `Code/Controllers/travelcore.dll` (Windows) або `libtravelcore.so` (Linux/macOS).

### 3. Консольний режим (без GUI)

```bat
cd Code
python Main.py --console DataBase\travel_db.json
REM або з демо-базою:  python Main.py --console Tests\sample_db.json
```

### 4. C++ smoke-тест (без Python і без JSON)

Демо-дані задані прямо в коді тесту (C++ ядро JSON не парсить):

```bat
cd Code\Tests
g++ -std=c++17 -Wall -Wextra -I ..\Models\Include -I ..\Controllers\Include smoke_test.cpp ..\Models\Src\*.cpp ..\Controllers\Src\Algorithms.cpp ..\Controllers\Src\TravelSystem.cpp -o smoke_test
smoke_test
REM або одразу зі скриптом збірки: Code\build.bat --tests / Code\test.bat  /  ./build.sh --tests
```

### 5. Збірка .exe через GitHub Actions

Workflow `.github/workflows/release.yml` збирає Windows-.exe з точки входу
`Code/Main.py` (PyInstaller, `--windowed`) на кожному пушу в `master` і вручну
(`workflow_dispatch`): zip `TravelSystemApp-win.zip` прикріплюється до артефактів
збірки у вкладці Actions. При пуші тега `v*` той самий zip автоматично
публікується як GitHub Release.

### 6. Наповнення бази даних

`Code/DataBase/travel_db.json` у репозиторії — порожній шаблон
(`{"cities": [], "destinations": [], "routes": []}`). Формат файлу та приклад
записів із кількома містами й дорогами зі смугами транспорту — у
`Code/DataBase/schema.md`; робочий приклад — `Code/Tests/sample_db.json`.

## Зауваження

- Шлях до бібліотеки можна задати вручну змінною середовища `TRAVELCORE_LIB`.
- У консолі Windows кирилиця може відображатися некоректно через кодову сторінку;
  використовуйте `set PYTHONUTF8=1` (у Docker уже задано `PYTHONUTF8=1`).
- C++ код компілюється з прапорцями `-Wall -Wextra -std=c++17` без попереджень.
