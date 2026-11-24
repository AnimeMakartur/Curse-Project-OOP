# Схема локальної бази даних (travel_db.json)

База даних — один JSON-файл (`travel_db.json`), автономне сховище без зовнішньої СУБД.
**Файл у репозиторії навмисно порожній (шаблонний)** — наповнення виконується окремим завданням.
Приклад наповненої бази з двома містами — у `Code/Tests/sample_db.json`.

## Структура

```json
{
  "cities": [ ... ],
  "destinations": [ ... ],
  "routes": [ ... ]
}
```

Усі туристичні об'єкти (`destinations`) та ребра транспортних графів (`routes`)
прив'язані до міста через `cityId`. Система працює **виключно в межах обраного
міста**: фільтрація, граф для Дейкстри та план не змішують дані різних міст.

## cities — міста / міські агломерації

| Поле          | Тип    | Опис                                                    |
| ------------- | ------ | ------------------------------------------------------- |
| `id`          | int    | унікальний ідентифікатор міста (ціле, унікальне в базі) |
| `name`        | string | назва міста / агломерації                               |
| `region`      | string | область / регіон (опціонально)                          |
| `description` | string | короткий опис агломерації (опціонально)                 |

## destinations — каталог туристичних об'єктів

Спільні поля для обох типів:

| Поле            | Тип      | Опис                                                                                                                                       |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `type`          | string   | `"attraction"`, `"museum"` або `"hotel"` (готель — стартова точка маршруту; сприймається як `attraction` із тегом `hotel`/`accommodation`) |
| `id`            | int      | унікальний ідентифікатор об'єкта (вершина графа маршрутів)                                                                                 |
| `cityId`        | int      | id міста, якому належить об'єкт (`cities[].id`)                                                                                            |
| `name`          | string   | назва                                                                                                                                      |
| `cost`          | double   | вартість вхідного квитка, EUR                                                                                                              |
| `rating`        | double   | рейтинг 0..5                                                                                                                               |
| `visitDuration` | double   | час огляду, год                                                                                                                            |
| `openHour`      | double   | година відкриття (напр. 9.0)                                                                                                               |
| `closeHour`     | double   | година закриття (напр. 18.0)                                                                                                               |
| `tags`          | string[] | теги категорій (мають перетинатися з інтересами туриста)                                                                                   |

Додаткові поля для `"attraction"`:

| Поле                 | Тип    | Опис                    |
| -------------------- | ------ | ----------------------- |
| `isOutdoor`          | bool   | відкрита пам'ятка чи ні |
| `architecturalStyle` | string | архітектурний стиль     |
| `isSeasonal`         | bool   | сезонний об'єкт чи ні   |

Додаткові поля для `"museum"`:

| Поле              | Тип    | Опис                 |
| ----------------- | ------ | -------------------- |
| `exhibitsCount`   | int    | кількість експонатів |
| `hasAudioGuide`   | bool   | наявність аудіогіда  |
| `expositionTheme` | string | тема експозиції      |

## routes — ребра мультимодального транспортного графа міста

Кожне ребро `(fromId, toId)` — ділянка дороги довжиною `distanceKm` у межах
одного міста (`cityId`) з набором доступних смуг/ліній `lanes`.

| Поле         | Тип    | Опис                                                 |
| ------------ | ------ | ---------------------------------------------------- |
| `cityId`     | int    | id міста, якому належить ділянка дороги              |
| `fromId`     | int    | id початкової вершини (об'єкта)                      |
| `toId`       | int    | id кінцевої вершини (об'єкта)                        |
| `distanceKm` | double | довжина ділянки, км                                  |
| `lanes`      | array  | доступні смуги/лінії: рядки або об'єкти (див. нижче) |

### lanes — смуги руху та лінії громадського транспорту

**Рядок** — скорочена форма, параметри беруться за замовчуванням для типу:

- `sidewalk` — пішохідний тротуар (5 км/год, безкоштовно)
- `bike_lane` — велодоріжка (15 км/год, безкоштовно)
- `car_lane` — загальна автомобільна смуга (30 км/год, безкоштовно)
- `bus_lane` — виділена автобусна смуга (бонус до швидкості ×1.3, ~0.30 EUR, очікування ~9 хв)
- `metrobus` — лінія метробуса / BRT (високий пріоритет, ×1.5, ~0.40 EUR, очікування ~6 хв)
- `tram_line` — швидкісний / відокремлений трамвай (×1.6, ~0.30 EUR, без заторів)
- `suburban_rail` — приміська електричка (70 км/год ×1.4, ~0.60 EUR, очікування ~15 хв)
- `railway` — міська залізниця (90 км/год ×1.6, ~0.90 EUR, максимальна швидкість на великі дистанції)

**Об'єкт** — повна форма з перевизначенням параметрів:

| Поле              | Тип    | Опис                                                                  |
| ----------------- | ------ | --------------------------------------------------------------------- |
| `type`            | string | один із типів вище (обов'язкове)                                      |
| `routeName`       | string | назва/номер маршруту, опціонально (напр. `"Tram 8"`, `"Metrobus M1"`) |
| `speedMultiplier` | double | коефіцієнт приросту швидкості `k_speed` (за замовчуванням — для типу) |
| `baseSpeedKmh`    | double | базова швидкість `v_base`, км/год                                     |
| `cost`            | double | вартість проїзду, EUR                                                 |
| `waitTimeHours`   | double | середній час очікування транспорту, год                               |

Час переміщення смугою/лінією `l` на ребрі довжиною `d`:

```
t = d / (baseSpeedKmh · speedMultiplier) + waitTimeHours
```

Алгоритм Дейкстри для ребра `(u, v)` обирає **оптимальну лінію** з мінімальним `t`
серед тих, чия `cost` вписується в залишок бюджету туриста:

```
t(u,v) = min over l in lanes, cost(l) <= budget:  d / (v_base·k_speed(l)) + t_wait(l)
```

## Приклад запису (див. також Code/Tests/sample_db.json)

```json
{
  "cities": [
    {
      "id": 1,
      "name": "Lviv",
      "region": "Lviv Oblast",
      "description": "Compact old town with a tram network"
    },
    {
      "id": 2,
      "name": "Kyiv",
      "region": "Kyiv Oblast",
      "description": "Megacity with a metrobus (BRT) and suburban trains"
    }
  ],
  "destinations": [
    {
      "type": "attraction",
      "id": 1,
      "cityId": 1,
      "name": "Rynok Square",
      "cost": 0,
      "rating": 4.8,
      "visitDuration": 1.5,
      "openHour": 0.0,
      "closeHour": 23.99,
      "tags": ["history", "architecture"],
      "isOutdoor": true,
      "architecturalStyle": "renaissance",
      "isSeasonal": false
    },
    {
      "type": "museum",
      "id": 2,
      "cityId": 1,
      "name": "Lviv History Museum",
      "cost": 1.6,
      "rating": 4.6,
      "visitDuration": 2.0,
      "openHour": 10.0,
      "closeHour": 18.0,
      "tags": ["history", "culture", "museums"],
      "exhibitsCount": 1200,
      "hasAudioGuide": true,
      "expositionTheme": "city history"
    }
  ],
  "routes": [
    {
      "cityId": 1,
      "fromId": 1,
      "toId": 2,
      "distanceKm": 0.4,
      "lanes": ["sidewalk", "bike_lane"]
    },
    {
      "cityId": 1,
      "fromId": 2,
      "toId": 3,
      "distanceKm": 1.2,
      "lanes": [
        { "type": "bus_lane", "routeName": "Bus 29", "cost": 0.3, "waitTimeHours": 0.15 },
        {
          "type": "tram_line",
          "routeName": "Tram 8",
          "speedMultiplier": 1.6,
          "baseSpeedKmh": 35,
          "cost": 0.3,
          "waitTimeHours": 0.12
        },
        "sidewalk"
      ]
    },
    {
      "cityId": 1,
      "fromId": 1,
      "toId": 4,
      "distanceKm": 12.0,
      "lanes": [
        {
          "type": "railway",
          "routeName": "City railway S1",
          "baseSpeedKmh": 90,
          "speedMultiplier": 1.6,
          "cost": 0.9,
          "waitTimeHours": 0.3
        },
        { "type": "suburban_rail", "routeName": "Suburban train 801", "cost": 0.6 },
        "car_lane"
      ]
    }
  ]
}
```
