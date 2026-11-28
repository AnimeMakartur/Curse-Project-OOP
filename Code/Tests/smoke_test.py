"""Smoke-тест ядра TravelSystem через Python-клієнт (ctypes → C++ DLL/SO).

Еквівалент колишнього C++ smoke_test.cpp: перевіряє повний цикл
наповнення бази → профіль туриста → фільтр → сортування → Дейкстра → план.
Запуск (після збірки ядра build.bat / build.sh):

    python Tests/smoke_test.py [шлях_до_sample_db.json]

За замовчуванням бере Tests/sample_db.json поруч зі скриптом.
"""

import json
import os
import sys

# Додаємо Code/View у sys.path, щоб імпортувати travel_client
_HERE = os.path.dirname(os.path.abspath(__file__))
_VIEW = os.path.normpath(os.path.join(_HERE, "..", "View"))
if _VIEW not in sys.path:
    sys.path.insert(0, _VIEW)

from travel_client import TravelClient  # noqa: E402

DEFAULT_DB = os.path.normpath(os.path.join(_HERE, "sample_db.json"))


def main():
    dbPath = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    with TravelClient() as client:
        client.loadData(dbPath)
        cities = client.getCities()
        print(
            f"Завантажено міст: {client.citiesCount()}, "
            f"об'єктів: {client.catalogSize()}, ребер графів: {client.routesCount()}"
        )
        for c in cities:
            print(
                f"  місто #{c['id']}: {c['name']} ({c.get('region', '')}) — "
                f"{c.get('description', '')}"
            )
        if not cities:
            print("База порожня — завершення без профілю.")
            return 0

        cityId = cities[0]["id"]
        client.setTourist("Єгор", 20, True, 2, 8.0, ["history", "architecture", "nature"], cityId=cityId, )
        profile = client.getProfile()
        print(
            f"\nПрофіль: {profile['name']}, місто id={profile['targetCityId']}, "
            f"денний бюджет: {profile['dailyBudget']}, загальний: {profile['totalBudget']}"
        )

        print(f"\nКаталог обраного міста #{cityId}:")
        for d in client.getCatalog(cityId):
            print(f"  id={d['id']} cityId={d['cityId']} [{d['type']}] {d['name']} — "
                f"{d['cost']} EUR, рейтинг {d['rating']}, {d['visitDuration']} год"
            )

        print("\nРебра графа міста (смуги/лінії):")
        for r in client.getRoutes(cityId):
            lanes = ", ".join(f"{l['type']}" + (f" «{l['routeName']}»" if l.get("routeName") else "")
                for l in r["lanes"]
            )
            print(f"  {r['fromId']} -> {r['toId']}: {r['distanceKm']} км | {lanes}")

        filtered = client.filterDestinations()
        print(f"\nВідфільтровано об'єктів міста #{cityId}: {len(filtered)}")
        sortedDests = client.sortedDestinations()
        for d in sortedDests:
            print(f"  [{d['relevance']:.4f}] id={d['id']} cityId={d['cityId']} "
                f"{d['details']}"
            )

        if len(sortedDests) >= 2:
            a, b = sortedDests[0]["id"], sortedDests[-1]["id"]
            print(f"\nНайкоротший шлях {client.destinationName(a)} -> "
                f"{client.destinationName(b)} (Дейкстра, бюджет {profile['dailyBudget']} EUR/day):"
            )
            path = client.findShortestPath(a, b)
            if not path:
                print("  немає шляху")
            for s in path:
                lane = s["lane"]
                name = f" «{lane['routeName']}»" if lane.get("routeName") else ""
                print(f"  {s.get('fromName', s['fromId'])} -> {s.get('toName', s['toId'])}: "
                    f"{s['distanceKm']} км, {s['timeHours']:.3f} год, {s['cost']} EUR — "
                    f"{lane['transportUkr']}{name} (еф. швидкість "
                    f"{lane['effectiveSpeedKmh']:g} км/год)"
                )

            # Контроль ізоляції міст: вершини різних міст не з'єднуються
            otherCityId = next((c["id"] for c in cities if c["id"] != cityId), None)
            if otherCityId is not None:
                otherDests = client.getCatalog(otherCityId)
                if otherDests:
                    d = otherDests[0]
                    cross = client.findShortestPath(a, d["id"], budget=1e9)
                    status = "немає шляху (OK)" if not cross else "Є ШЛЯХ (ПОМИЛКА!)"
                    print(f"  контроль: шлях {a} (місто {cityId}) -> {d['id']} "
                        f"(місто {otherCityId}): {status}"
                    )

        plan = client.generatePlan()
        print("\n" + plan.get("summary", ""))
        print("План (JSON):", json.dumps(plan, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
