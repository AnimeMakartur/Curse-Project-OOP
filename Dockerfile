# TravelSystem — автономна інформаційно-аналітична система підбору туристичного плану.
# Один контейнер: C++17 ядро (libtravelcore.so) + Python/PyQt6 GUI + JSON-база.
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUTF8=1 \
    PYTHONUNBUFFERED=1

# Компілятор C++17, make та runtime-бібліотеки для роботи PyQt6 у X11/Wayland
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    make \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    libfontconfig1 \
    libdbus-1-3 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxcb-image0 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python-залежності (PyQt6)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Вихідний код та збірка C++ ядра у динамічну бібліотеку libtravelcore.so
COPY Code ./Code
RUN cd Code && chmod +x build.sh && ./build.sh

# Змінні середовища: шлях до бібліотеки ядра, UTF-8, Qt-платформа.
# QT_QPA_PLATFORM можна перевизначити (напр. offscreen для headless-тестів).
ENV TRAVELCORE_LIB=/app/Code/Controllers/libtravelcore.so \
    PYTHONUTF8=1 \
    QT_QPA_PLATFORM=xcb

# Базу даних змонтовано як volume у docker-compose.yml:
# зміни у Code/DataBase/travel_db.json підхоплюються без перезбірки.
CMD ["python", "Code/View/app.py", "/app/Code/DataBase/travel_db.json"]
