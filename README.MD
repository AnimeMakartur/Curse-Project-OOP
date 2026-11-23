# TravelSystem — програмне забезпечення для автоматичного персоналізованого підбору туристичного плану

Курсовий проєкт з дисципліни «Об'єктно-орієнтоване програмування».
Автономна інформаційно-аналітична система (CARS): будує персоналізований
туристичний план з урахуванням бюджету, часу, годин роботи об'єктів та
інтересів туриста.

## Архітектура (три шари)

| Шар | Мова | Папка | Призначення |
|---|---|---|---|
| Представлення (GUI) | Python (tkinter) | `Code/View` | Віконний інтерфейс, валідація вводу, відображення результатів |
| Бізнес-логіка / обчислювальне ядро | C++17 | `Code/Controllers`, `Code/Models` | Алгоритми (лінійний пошук, сортування, Дейкстра), фасад `TravelSystem` |
| Дані та міжмовна взаємодія | JSON + C API | `Code/DataBase` | Локальна база `travel_db.json`, завантажувач, C API (`c_api.cpp`) |

Міжмовна взаємодія: Python GUI викликає методи C++ ядра через динамічну
бібліотеку (`travelcore.dll` / `libtravelcore.so`) засобами `ctypes`.
Результати C++ повертає у вигляді JSON-рядків.

## Структура проєкту

```
Code/
├── Models/                  # класи предметної області (діаграма класів, рис. 2.2)
│   ├── Tourist.*            #   турист: бюджет (денний/загальний), дні, інтереси
│   ├── TouristDestination.* #   абстрактний базовий клас об'єкта (protected-поля)
│   ├── Attraction.*         #   пам'ятка (успадкування, поліморфізм)
│   ├── Museum.*             #   музей (успадкування, поліморфізм)
│   ├── Route.*              #   ребро графа + дорога як масив полос (lanes)
│   └── TravelPlan.*         #   результат: розклад по днях, метрики, експорт
├── Controllers/             # керуюче ядро
│   ├── Algorithms.*         #   лінійний пошук, сортування, Дейкстра (пріоритетна черга)
│   ├── TravelSystem.*       #   фасад: loadData, filter, sort, generatePersonalizedPlan, findShortestPath
│   └── c_api.cpp            #   extern "C" API для ctypes (ts_create, ts_generate_plan, ...)
├── DataBase/
│   ├── JsonParser.h         #   мінімальний JSON-парсер без залежностей
│   ├── DataLoader.*         #   читання travel_db.json у каталог та граф
│   ├── travel_db.json       #   ПОРОЖНЯ база (наповнюється окремим завданням, див. schema.md)
│   └── schema.md            #   опис формату БД і приклад записів
├── View/
│   ├── travel_client.py     #   ctypes-обгортка над C API
│   └── app.py               #   GUI (tkinter) + консольний режим --console
├── Tests/smoke_test.cpp     #   консольний тест ядра без GUI
├── build.bat                #   збірка DLL (Windows: g++ / clang++ / MSVC cl)
└── build.sh                 #   збірка .so (Linux/macOS: g++ / clang++)
```

## Класи (відповідно до діаграми класів)

- `Tourist` — `getDailyBudget()` (формула 1.7), `getTotalBudget()` (1.8), `getInterests()`, `updateProfile(...)`
- `TravelSystem` — фасад: `loadData`, `setTouristProfile`, `filterDestinations` (лінійний пошук),
  `sortDestinations` (релевантність, формула 1.4), `generatePersonalizedPlan`, `findShortestPath` (Дейкстра)
- `TouristDestination` (abstract) — `isOpen`, поліморфні `calculateRelevance`, `getDetails`
- `Attraction`, `Museum` — похідні класи
- `Route` — ребро графа; **доповнення:** поле `lanes` — дорога як масив полос,
  кожна полоса свого типу: `sidewalk` (тротуар), `bike_lane` (велодоріжка),
  `car_lane` (автомобільна смуга), `bus_lane` (автобусна смуга),
  `tram_line` (відокремлена лінія трамвая), `railway` (залізнична колія)
- `TravelPlan` — `addDayStep`, `calculateTotalMetrics`, `exportPlanSummary`

## Вимоги

- Windows: Python 3.8+ (стандартний, з tkinter) та один із компіляторів C++17:
  MinGW/MSYS2 (`g++`), LLVM (`clang++`) або MSVC Build Tools (`cl`).
- Linux/macOS: Python 3.8+ та `g++`/`clang++`.

## Розгортання та запуск

### 1. Зібрати ядро C++ у shared-бібліотеку

Windows (з кореня проєкту):

```bat
Code\build.bat
```

→ з'явиться `Code\Controllers\travelcore.dll`.

Linux/macOS:

```bash
cd Code && ./build.sh        # або chmod +x build.sh
```

→ з'явиться `Code\Controllers\libtravelcore.so`.

### 2. (Необов'язково) наповнити базу даних

`Code/DataBase/travel_db.json` навмисно порожній — наповнення виконується
окремим завданням. Формат файлу та приклад записів — у `Code/DataBase/schema.md`.

### 3. Запустити GUI

```bat
cd Code\View
python app.py
```

У вікні: вказати профіль туриста → «Завантажити базу даних» →
«Застосувати профіль» → «Згенерувати персоналізований план».

### 4. Консольна перевірка (без GUI)

```bat
cd Code\View
python app.py --console ..\DataBase\travel_db.json
```

### 5. Консольний тест ядра C++ (без Python)

```bat
cd Code\Tests
g++ -std=c++17 -I ..\Models -I ..\DataBase -I ..\Controllers smoke_test.cpp ..\Models\*.cpp ..\DataBase\DataLoader.cpp ..\Controllers\Algorithms.cpp ..\Controllers\TravelSystem.cpp -o smoke_test
smoke_test ..\DataBase\travel_db.json
```

## Зауваження

- Шлях до бібліотеки можна задати вручну змінною середовища `TRAVELCORE_LIB`.
- У консолі Windows кирилиця може відображатися некоректно через кодову сторінку;
  у GUI та JSON-виводі все коректно (UTF-8). За потреби: `set PYTHONUTF8=1`.
