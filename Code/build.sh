#!/usr/bin/env bash
# Збірка ядра C++ у shared-бібліотеку Controllers/libtravelcore.so
# Потрібен g++ або clang++ (C++17). Прапорець --tests додатково збирає smoke-тест.
set -euo pipefail
cd "$(dirname "$0")"

CXX="${CXX:-g++}"
command -v "$CXX" >/dev/null 2>&1 || CXX=clang++

SOURCES=(
    Models/Src/City.cpp Models/Src/Lane.cpp Models/Src/PathStep.cpp Models/Src/Tourist.cpp
    Models/Src/TouristDestination.cpp Models/Src/Attraction.cpp Models/Src/Museum.cpp
    Models/Src/Route.cpp Models/Src/TravelPlan.cpp
    Controllers/Src/Algorithms.cpp Controllers/Src/TravelSystem.cpp Controllers/Src/c_api.cpp
)

"$CXX" -std=c++17 -O2 -Wall -Wextra -fPIC -shared \
    -static-libgcc -static-libstdc++ \
    -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH \
    -I Models/Include -I Controllers/Include \
    "${SOURCES[@]}" \
    -o Controllers/libtravelcore.so

echo "Готово: Controllers/libtravelcore.so"

if [[ "${1:-}" == "--tests" ]]; then
    mkdir -p Tests/.build
    "$CXX" -std=c++17 -O2 -Wall -Wextra \
        -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH \
        -I Models/Include -I Controllers/Include \
        Tests/smoke_test.cpp "${SOURCES[@]}" \
        -o Tests/.build/smoke_test
    echo "Готово: Tests/.build/smoke_test (запуск: Tests/.build/smoke_test)"
fi
