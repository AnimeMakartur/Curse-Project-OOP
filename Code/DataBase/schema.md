# Схема локальної бази даних (travel_db.json)

База даних — один JSON-файл (`travel_db.json`), автономне сховище без зовнішньої СУБД.
**Файл у репозиторії навмисно порожній** — наповнення виконується окремим завданням.

## Структура

```json
{
  "destinations": [ ... ],
  "routes": [ ... ]
}
```

## destinations — каталог туристичних об'єктів

Спільні поля для обох типів:

| Поле | Тип | Опис |
|---|---|---|
| `type` | string | `"attraction"` або `"museum"` |
| `id` | int | унікальний ідентифікатор (вершина графа) |
| `name` | string | назва |
| `cost` | double | вартість вхідного квитка, грн |
| `rating` | double | рейтинг 0..5 |
| `visitDuration` | double | час огляду, год |
| `openHour` | double | година відкриття (напр. 9.0) |
| `closeHour` | double | година закриття (напр. 18.0) |
| `tags` | string[] | теги категорій (мають перетинатися з інтересами туриста) |

Додаткові поля для `"attraction"`:

| Поле | Тип | Опис |
|---|---|---|
| `isOutdoor` | bool | відкрита пам'ятка чи ні |
| `architecturalStyle` | string | архітектурний стиль |
| `isSeasonal` | bool | сезонний об'єкт чи ні |

Додаткові поля для `"museum"`:

| Поле | Тип | Опис |
|---|---|---|
| `exhibitsCount` | int | кількість експонатів |
| `hasAudioGuide` | bool | наявність аудіогіда |
| `expositionTheme` | string | тема експозиції |

## routes — ребра графа маршрутів

| Поле | Тип | Опис |
|---|---|---|
| `fromId` | int | id початкової вершини |
| `toId` | int | id кінцевої вершини |
| `distanceKm` | double | відстань, км |
| `travelTimeHours` | double | час у дорозі, год |
| `transportCost` | double | вартість проїзду, грн |
| `dailyTimeLimit` | double | денний ліміт часу (з профілю) |
| `lanes` | string[] | **дорога як масив полос**: тип кожної полоси |

Допустимі значення `lanes` (по одній на полосу, порядок = порядок полос на дорозі):

- `sidewalk` — тротуар
- `bike_lane` — велосипедна доріжка
- `car_lane` — автомобільна смуга
- `bus_lane` — автобусна смуга
- `tram_line` — відокремлена лінія трамвая
- `railway` — залізнична колія

## Приклад запису (для наповнення БД окремим завданням)

```json
{
  "destinations": [
    {
      "type": "attraction",
      "id": 1,
      "name": "Ратуша",
      "cost": 50,
      "rating": 4.7,
      "visitDuration": 1.0,
      "openHour": 9.0,
      "closeHour": 18.0,
      "tags": ["історія", "архітектура"],
      "isOutdoor": false,
      "architecturalStyle": "бароко",
      "isSeasonal": false
    },
    {
      "type": "museum",
      "id": 2,
      "name": "Музей історії міста",
      "cost": 80,
      "rating": 4.5,
      "visitDuration": 2.0,
      "openHour": 10.0,
      "closeHour": 17.0,
      "tags": ["історія", "культура"],
      "exhibitsCount": 1200,
      "hasAudioGuide": true,
      "expositionTheme": "історія міста"
    }
  ],
  "routes": [
    {
      "fromId": 1,
      "toId": 2,
      "distanceKm": 0.4,
      "travelTimeHours": 0.15,
      "transportCost": 0,
      "dailyTimeLimit": 8.0,
      "lanes": ["sidewalk", "bike_lane"]
    },
    {
      "fromId": 2,
      "toId": 3,
      "distanceKm": 3.1,
      "travelTimeHours": 0.5,
      "transportCost": 25,
      "dailyTimeLimit": 8.0,
      "lanes": ["bus_lane", "sidewalk"]
    }
  ]
}
```
