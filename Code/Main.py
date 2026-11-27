"""Головна точка входу TravelSystem (корінь папки Code).

Запуск програми завжди йде звідси — і з сирців, і зі зібраного .exe:

    python Main.py                  — GUI (PyQt6), база DataBase/travel_db.json
    python Main.py <файл_бд.json>   — GUI з вказаною базою
    python Main.py --console [бд]   — консольний режим (без вікна)

.exe збирається через GitHub Actions (PyInstaller, див.
.github/workflows/release.yml) саме з цього файла.

Базу даних JSON парсить готовий парсер Python (стандартний модуль json,
див. View/db_loader.py); C++ ядро отримує вже розібрані дані через C API.
"""

import os
import sys

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEW_DIR = os.path.join(CODE_DIR, "View")
if VIEW_DIR not in sys.path:
    # Режим запуску з сирців: модулі представлення лежать у View/.
    # У зібраному PyInstaller-exe вони вже вбудовані в архів (див. --paths у workflow).
    sys.path.insert(0, VIEW_DIR)

from app import main  # імпорт після налаштування sys.path

if __name__ == "__main__":
    main()
