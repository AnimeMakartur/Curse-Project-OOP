"""Точка входу TravelSystem (шар представлення, Python + PyQt6).

Запуск GUI:        python app.py [шлях_до_db.json]
Консольний режим:  python app.py --console [шлях_до_db.json]

База даних завантажується автоматично при старті зі шляху за замовчуванням
(../DataBase/travel_db.json) — без кнопок і діалогів вибору файла.
"""

import json
import os
import sys

from travel_client import TravelClient, appBaseDir

DefaultDb = os.path.join(appBaseDir(), "..", "DataBase", "travel_db.json")


def runConsole(dbPath):
    """Консольна демонстрація роботи без GUI (для перевірки після збірки)."""
    with TravelClient() as client:
        client.loadData(dbPath)
        cities = client.getCities()
        print(
            f"Завантажено міст: {client.citiesCount()}, "
            f"об'єктів: {client.catalogSize()}, ребер графів: {client.routesCount()}"
        )
        for c in cities:
            print(
                f"  місто #{c['id']}: {c['name']} ({c.get('region', '')}) — {c.get('description', '')}"
            )
        if not cities:
            print(
                "База порожня — додайте міста, об'єкти та маршрути у travel_db.json (див. schema.md)"
            )
            return 0

        cityId = cities[0]["id"]
        client.setTourist(
            "Єгор",
            20,
            True,
            2,
            8.0,
            ["history", "architecture", "nature"],
            cityId=cityId,
        )
        print("\nПрофіль:", json.dumps(client.getProfile(), ensure_ascii=False, indent=2))

        print("\nКаталог обраного міста:")
        for d in client.getCatalog(cityId):
            print(
                f"  id={d['id']} cityId={d['cityId']} [{d['type']}] {d['name']} — "
                f"{d['cost']} EUR, рейтинг {d['rating']}, {d['visitDuration']} год"
            )

        print("\nРебра графа міста (смуги/лінії):")
        for r in client.getRoutes(cityId):
            lanes = ", ".join(
                f"{l['type']}" + (f" «{l['routeName']}»" if l.get("routeName") else "")
                for l in r["lanes"]
            )
            print(f"  {r['fromId']} -> {r['toId']}: {r['distanceKm']} км | {lanes}")

        print(
            "\nФільтр (лінійний пошук):",
            json.dumps(client.filterDestinations(), ensure_ascii=False, indent=2),
        )
        print(
            "\nСортовано за релевантністю:",
            json.dumps(client.sortedDestinations(), ensure_ascii=False, indent=2),
        )

        filtered = client.filterDestinations()
        if len(filtered) >= 2:
            a, b = filtered[0]["id"], filtered[-1]["id"]
            path = client.findShortestPath(a, b)
            print(
                f"\nНайкоротший шлях {client.destinationName(a)} -> {client.destinationName(b)}"
                " (Дейкстра, деталізація по лініях):"
            )
            for s in path:
                lane = s["lane"]
                name = f" «{lane['routeName']}»" if lane.get("routeName") else ""
                print(
                    f"  {s.get('fromName', s['fromId'])} -> {s.get('toName', s['toId'])}: "
                    f"{s['distanceKm']} км, "
                    f"{s['timeHours']:.3f} год, {s['cost']} EUR — "
                    f"{lane['transportUkr']}{name}"
                )

        plan = client.generatePlan()
        print("\n" + plan.get("summary", ""))
        print("\nПлан (JSON):", json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def _displayReachable():
    """Груба перевірка доступності X-дисплея до старту Qt (щоб не падати з qpa-xcb)."""
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    display = os.environ.get("DISPLAY", "")
    if not display:
        return False
    if display.startswith("unix:"):
        display = display[len("unix:") :]
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


def runGui(dbPath=None):
    from PyQt6.QtWidgets import QApplication

    from main_window import AppStyleSheet, MainWindow

    # Headless-fallback актуальний лише на Linux/X11: якщо дисплей не задано/недоступний —
    # не падаємо з "could not connect to display", а переходимо в offscreen із попередженням.
    # На Windows (os.name == "nt") Qt сам використовує рідний плагін "windows", тому
    # перевірку DISPLAY пропускаємо — інакше GUI на голій Windows завжди ставав би offscreen.
    # Перевіряємо навіть коли QT_QPA_PLATFORM=xcb задано примусово (Dockerfile/compose).
    qpa = os.environ.get("QT_QPA_PLATFORM", "")
    if os.name != "nt" and qpa in ("", "xcb", "wayland", "wayland-egl") and not _displayReachable():
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        print(
            "Увага: X-дисплей недоступний (DISPLAY=%r, WAYLAND_DISPLAY=%r) — GUI запущено "
            "у headless-режимі QT_QPA_PLATFORM=offscreen. Для повноцінного GUI на Linux — "
            "DISPLAY=:0 (сокет /tmp/.X11-unix прокидається docker-compose); у Docker під "
            "Windows — VcXsrv/Xming + .env DISPLAY=host.docker.internal:0."
            % (os.environ.get("DISPLAY", ""), os.environ.get("WAYLAND_DISPLAY", ""))
        )

    app = QApplication(sys.argv)
    app.setApplicationName("TravelSystem")
    app.setStyleSheet(AppStyleSheet)
    window = MainWindow(dbPath=dbPath)
    window.show()
    return app.exec()


def main():
    args = sys.argv[1:]
    if "--console" in args:
        idx = args.index("--console")
        db = args[idx + 1] if idx + 1 < len(args) else os.path.normpath(DefaultDb)
        sys.exit(runConsole(db))
    db = args[0] if args else os.path.normpath(DefaultDb)
    sys.exit(runGui(db))


if __name__ == "__main__":
    main()
