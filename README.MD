# TravelSystem — програмне забезпечення для автоматичного персоналізованого підбору туристичного плану

Курсовий проєкт з дисципліни «Об'єктно-орієнтоване програмування».
Автономна інформаційно-аналітична система (CARS): будує персоналізований
туристичний план **в межах обраного міста/агломерації** з урахуванням бюджету,
часу, годин роботи об'єктів, інтересів туриста та **мультимодальної транспортної
мережі** (смуги руху й лінії громадського транспорту на кожній ділянці дороги).

## Архітектура (три шари)

| Шар | Мова | Папка | Призначення |
|---|---|---|---|
| Представлення (GUI) | Python 3 + **PyQt6** | `Code/View` | Віконний інтерфейс: вибір міста, профіль туриста, каталог (QTableWidget), план по днях, метрики; консольний режим `--console` |
| Бізнес-логіка / обчислювальне ядро | **C++17** | `Code/Controllers`, `Code/Models` | Моделі предметної області, алгоритми (лінійний пошук, сортування, Дейкстра з чергою з пріоритетом), фасад `TravelSystem` |
| Дані та міжмовна взаємодія | JSON + C API | `Code/DataBase`, `Controllers/c_api.cpp` | Локальна база `travel_db.json` (міста + об'єкти + графи), завантажувач `DataLoader`, `extern "C"` API для ctypes |

Міжмовна взаємодія: Python GUI викликає методи C++ ядра через динамічну
бібліотеку (`travelcore.dll` / `libtravelcore.so`) засобами `ctypes`
(`Code/View/travel_client.py`). Усі результати C++ повертає у вигляді JSON-рядків.

Потік даних: `PyQt6 GUI → ctypes → C API (c_api.cpp) → TravelSystem → Algorithms/DataLoader → JSON DB`.

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
    ├── Models/                  # класи предметної області (ООП)
    │   ├── City.*               #   місто/агломерація (id, назва, регіон, опис)
    │   ├── Tourist.*            #   турист: targetCityId, бюджет (денний/загальний), дні, інтереси
    │   ├── TouristDestination.* #   абстрактний базовий клас об'єкта (cityId, protected-поля)
    │   ├── Attraction.*         #   пам'ятка (успадкування, поліморфізм)
    │   ├── Museum.*             #   музей (успадкування, поліморфізм)
    │   ├── Lane.*               #   смуга/лінія: тип, маршрут, k_speed, v_base, cost, waitTime
    │   ├── Route.*              #   ребро графа: cityId, distanceKm, набір lanes, вибір найкращої лінії
    │   ├── PathStep.*           #   крок маршруту: ребро + обрана лінія + час + вартість
    │   └── TravelPlan.*         #   план по днях (DayItem: об'єкт + transfers), метрики, експорт
    ├── Controllers/             # керуюче ядро
    │   ├── Algorithms.*         #   лінійний пошук, сортування, Дейкстра (пріоритетна черга, вибір лінії)
    │   ├── TravelSystem.*       #   фасад: міста, фільтрація за targetCityId, план, findShortestPath
    │   └── c_api.cpp            #   extern "C" API для ctypes (ts_get_cities, ts_set_tourist, ts_generate_plan, ...)
    ├── DataBase/
    │   ├── JsonParser.h         #   мінімальний JSON-парсер без залежностей
    │   ├── DataLoader.*         #   читання travel_db.json: міста, каталог, графи зі смугами
    │   ├── travel_db.json       #   ПОРОЖНЯ шаблонна база (наповнюється окремо, див. schema.md)
    │   └── schema.md            #   опис формату БД і приклад записів
    ├── View/
    │   ├── travel_client.py     #   ctypes-обгортка над C API
    │   ├── main_window.py       #   головне вікно PyQt6 (каталог, план, метрики, шлях)
    │   └── app.py               #   точка входу: GUI (PyQt6) або --console
    ├── Tests/
    │   ├── smoke_test.cpp       #   консольний тест ядра без GUI
    │   └── sample_db.json       #   демо-база з двома містами для smoke-тесту
    ├── build.bat                #   збірка DLL (Windows: g++ / clang++ / MSVC cl), прапорець --tests
    └── build.sh                 #   збірка .so (Linux/macOS: g++ / clang++), прапорець --tests
```

## Класи (відповідно до діаграми класів, розширено)

- `City` — місто/агломерація: `id`, `name`, `region`, `description`.
- `Tourist` — `targetCityId`, `getDailyBudget()` (формула 1.7), `getTotalBudget()` (1.8), `getInterests()`, `updateProfile(...)`.
- `TravelSystem` — фасад: `loadData` (міста + каталог + графи), `getCities`, `setTouristProfile`,
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

### 1. Docker / Docker Compose — однією командою

```bash
docker compose up --build          # збірка образу + запуск GUI
```

- Linux: X11-дисплей хоста прокидається через `DISPLAY` і сокет `/tmp/.X11-unix`
  (для Wayland задайте `WAYLAND_DISPLAY` і `XDG_RUNTIME_DIR` у `.env`).
- Windows (WSL2 + VcXsrv/Xming): скопіюйте `.env.example` у `.env`, задайте
  `DISPLAY=host.docker.internal:0`, запустіть VcXsrv із **«Disable access control»**,
  потім `docker compose up --build`.
- Headless/CI: `QT_QPA_PLATFORM=offscreen docker compose up --build`.
- Консольний режим у контейнері: `docker compose --profile console run --build console`.

### Часті проблеми Docker

- `qt.qpa.xcb: could not connect to display` — контейнер не дістався до X-сервера
  (у логу видно значення `DISPLAY`; порожнє означає, що `.env`/змінна не підхопились).
  На Windows це нормально без `.env`: вкажіть `DISPLAY=host.docker.internal:0`
  (VcXsrv має слухати TCP 6000 і бути запущеним із «Disable access control»).
  На Linux перевірте `xhost` (дозвольте локальні підключення) — сокет уже прокинутий.
  Якщо дисплей недоступний, `app.py` **автоматично** переходить у
  `QT_QPA_PLATFORM=offscreen` із попередженням у логу (GUI тоді не видно, але застосунок
  не падає) — перевірено юніт-перевіркою `_display_reachable()`.
- `From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed...` — у Dockerfile встановлено
  `libxcb-cursor0` (є self-check `ldconfig -p | grep libxcb-cursor`); якщо бачите це
  разом із «could not connect to display» — спершу фіксніть дисплей, це вторинне
  повідомление плагіна xcb.
- `env: 'bash\r': No such file or directory` — CRLF у `build.sh`; уже виправлено
  (LF + `.gitattributes` + виклик `bash build.sh` у Dockerfile).
- Папка `Code/DataBase` змонтована як volume — зміни у `travel_db.json`
  підхоплюються без перезбірки контейнера.
- Консольний режим у контейнері: `docker compose --profile console run --build console`.

### 2. Локальна збірка та запуск

Windows (з кореня проєкту):

```bat
Code\build.bat            REM або Code\build.bat --tests — ще й smoke-тест
cd Code\View
python app.py              REM GUI (потрібен pip install -r ..\..\requirements.txt)
```

Linux/macOS:

```bash
cd Code && chmod +x build.sh && ./build.sh        # або ./build.sh --tests
cd View && python app.py
```

→ з'явиться `Code/Controllers/travelcore.dll` (Windows) або `libtravelcore.so` (Linux/macOS).

### 3. Консольний режим (без GUI)

```bat
cd Code\View
python app.py --console ..\DataBase\travel_db.json
REM або з демо-базою:  python app.py --console ..\Tests\sample_db.json
```

### 4. C++ smoke-тест (без Python)

```bat
cd Code\Tests
g++ -std=c++17 -Wall -Wextra -I ..\Models -I ..\DataBase -I ..\Controllers smoke_test.cpp ..\Models\*.cpp ..\DataBase\DataLoader.cpp ..\Controllers\Algorithms.cpp ..\Controllers\TravelSystem.cpp -o smoke_test
smoke_test sample_db.json
REM або одразу зі скриптом збірки: Code\build.bat --tests  /  ./build.sh --tests
```

### 5. Наповнення бази даних

`Code/DataBase/travel_db.json` у репозиторії — порожній шаблон
(`{"cities": [], "destinations": [], "routes": []}`). Формат файлу та приклад
записів із кількома містами й дорогами зі смугами транспорту — у
`Code/DataBase/schema.md`; робочий приклад — `Code/Tests/sample_db.json`.

## Зауваження

- Шлях до бібліотеки можна задати вручну змінною середовища `TRAVELCORE_LIB`.
- У консолі Windows кирилиця може відображатися некоректно через кодову сторінку;
  використовуйте `set PYTHONUTF8=1` (у Docker уже задано `PYTHONUTF8=1`).
- C++ код компілюється з прапорцями `-Wall -Wextra -std=c++17` без попереджень.
