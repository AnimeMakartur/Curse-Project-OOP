#!/usr/bin/env bash
# Збірка ядра C++ у shared-бібліотеку Controllers/libtravelcore.so
# Потрібен g++ або clang++ (C++17). Прапорець --tests додатково збирає smoke-тест.
set -euo pipefail
cd "$(dirname "$0")"

CXX="${CXX:-g++}"
command -v "$CXX" >/dev/null 2>&1 || CXX=clang++

SOURCES=(
    Models/City.cpp Models/Lane.cpp Models/PathStep.cpp Models/Tourist.cpp
    Models/TouristDestination.cpp Models/Attraction.cpp Models/Museum.cpp
    Models/Route.cpp Models/TravelPlan.cpp
    DataBase/DataLoader.cpp
    Controllers/Algorithms.cpp Controllers/TravelSystem.cpp Controllers/c_api.cpp
)

"$CXX" -std=c++17 -O2 -Wall -Wextra -fPIC -shared \
    -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH \
    -I Models -I DataBase -I Controllers \
    "${SOURCES[@]}" \
    -o Controllers/libtravelcore.so

echo "Готово: Controllers/libtravelcore.so"

if [[ "${1:-}" == "--tests" ]]; then
    mkdir -p Tests/.build
    "$CXX" -std=c++17 -O2 -Wall -Wextra \
        -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH \
        -I Models -I DataBase -I Controllers \
        Tests/smoke_test.cpp "${SOURCES[@]}" \
        -o Tests/.build/smoke_test
    echo "Готово: Tests/.build/smoke_test (запуск: Tests/.build/smoke_test Tests/sample_db.json)"
fi
