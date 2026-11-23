"""Точка входу TravelSystem (шар представлення, Python + PyQt6).

Запуск GUI:        python app.py [шлях_до_db.json]
Консольний режим:  python app.py --console [шлях_до_db.json]
"""

import json
import os
import sys

from travel_client import TravelClient

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "DataBase", "travel_db.json"
)


def run_console(db_path):
    """Консольна демонстрація роботи без GUI (для перевірки після збірки)."""
    with TravelClient() as client:
        client.load_data(db_path)
        cities = client.get_cities()
        print(f"Завантажено міст: {client.cities_count()}, "
              f"об'єктів: {client.catalog_size()}, ребер графів: {client.routes_count()}")
        for c in cities:
            print(f"  місто #{c['id']}: {c['name']} ({c.get('region', '')}) — {c.get('description', '')}")
        if not cities:
            print("База порожня — додайте міста, об'єкти та маршрути у travel_db.json (див. schema.md)")
            return 0

        city_id = cities[0]["id"]
        client.set_tourist(
            "Єгор", 1000, True, 2, 8.0,
            ["історія", "архітектура", "природа"],
            city_id=city_id,
        )
        print("\nПрофіль:", json.dumps(client.get_profile(), ensure_ascii=False, indent=2))

        print("\nКаталог обраного міста:")
        for d in client.get_catalog(city_id):
            print(f"  id={d['id']} cityId={d['cityId']} [{d['type']}] {d['name']} — "
                  f"{d['cost']} грн, рейтинг {d['rating']}, {d['visitDuration']} год")

        print("\nРебра графа міста (смуги/лінії):")
        for r in client.get_routes(city_id):
            lanes = ", ".join(
                f"{l['type']}" + (f" «{l['routeName']}»" if l.get("routeName") else "")
                for l in r["lanes"]
            )
            print(f"  {r['fromId']} -> {r['toId']}: {r['distanceKm']} км | {lanes}")

        print("\nФільтр (лінійний пошук):",
              json.dumps(client.filter_destinations(), ensure_ascii=False, indent=2))
        print("\nСортовано за релевантністю:",
              json.dumps(client.sorted_destinations(), ensure_ascii=False, indent=2))

        filtered = client.filter_destinations()
        if len(filtered) >= 2:
            a, b = filtered[0]["id"], filtered[-1]["id"]
            path = client.find_shortest_path(a, b)
            print(f"\nНайкоротший шлях {a} -> {b} (Дейкстра, деталізація по лініях):")
            for s in path:
                lane = s["lane"]
                name = f" «{lane['routeName']}»" if lane.get("routeName") else ""
                print(f"  {s['fromId']} -> {s['toId']}: {s['distanceKm']} км, "
                      f"{s['timeHours']:.3f} год, {s['cost']} грн — "
                      f"{lane['transportUkr']}{name}")

        plan = client.generate_plan()
        print("\n" + plan.get("summary", ""))
        print("\nПлан (JSON):", json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def _display_reachable():
    """Груба перевірка доступності X-дисплея до старту Qt (щоб не падати з qpa-xcb)."""
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    display = os.environ.get("DISPLAY", "")
    if not display:
        return False
    if display.startswith("unix:"):
        display = display[len("unix:"):]
    host, sep, num = display.rpartition(":")
    if not sep:
        return False
    try:
        n = int(num.split(".")[0])
    except ValueError:
        return False
    if host in ("", "unix"):
        return os.path.exists(f"/tmp/.X11-unix/X{n}")
    import socket
    try:
        with socket.create_connection((host, 6000 + n), timeout=1.5):
            return True
    except OSError:
        return False


def run_gui(db_path=None):
    from PyQt6.QtWidgets import QApplication

    from main_window import MainWindow

    # Якщо дисплей не задано/недоступний — не падаємо з "could not connect to display",
    # а переходимо в headless-режим offscreen із попередженням у лог.
    # Перевіряємо навіть коли QT_QPA_PLATFORM=xcb задано примусово (Dockerfile/compose).
    qpa = os.environ.get("QT_QPA_PLATFORM", "")
    if qpa in ("", "xcb", "wayland", "wayland-egl") and not _display_reachable():
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        print(
            "Увага: X-дисплей недоступний (DISPLAY=%r, WAYLAND_DISPLAY=%r) — GUI запущено "
            "у headless-режимі QT_QPA_PLATFORM=offscreen. Для повноцінного GUI: Windows — "
            "VcXsrv/Xming + .env DISPLAY=host.docker.internal:0; Linux — DISPLAY=:0 "
            "(сокет /tmp/.X11-unix прокидається docker-compose)." % (
                os.environ.get("DISPLAY", ""), os.environ.get("WAYLAND_DISPLAY", ""))
        )

    app = QApplication(sys.argv)
    app.setApplicationName("TravelSystem")
    window = MainWindow(db_path=db_path)
    window.show()
    return app.exec()


def main():
    args = sys.argv[1:]
    if "--console" in args:
        idx = args.index("--console")
        db = args[idx + 1] if idx + 1 < len(args) else os.path.normpath(DEFAULT_DB)
        sys.exit(run_console(db))
    db = args[0] if args else os.path.normpath(DEFAULT_DB)
    sys.exit(run_gui(db))


if __name__ == "__main__":
    main()
