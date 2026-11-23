#!/usr/bin/env bash
# Збірка ядра C++ у shared-бібліотеку Controllers/libtravelcore.so
# Потрібен g++ або clang++ (C++17).
set -euo pipefail
cd "$(dirname "$0")"

CXX="${CXX:-g++}"
command -v "$CXX" >/dev/null 2>&1 || CXX=clang++

"$CXX" -std=c++17 -O2 -fPIC -shared \
    -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH \
    -I Models -I DataBase -I Controllers \
    Models/Tourist.cpp Models/TouristDestination.cpp Models/Attraction.cpp \
    Models/Museum.cpp Models/Route.cpp Models/TravelPlan.cpp \
    DataBase/DataLoader.cpp \
    Controllers/Algorithms.cpp Controllers/TravelSystem.cpp Controllers/c_api.cpp \
    -o Controllers/libtravelcore.so

echo "Готово: Controllers/libtravelcore.so"
