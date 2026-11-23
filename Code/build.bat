@echo off
chcp 65001 >nul
REM Збірка ядра C++ у shared-бібліотеку Controllers\travelcore.dll
REM Порядок пошуку компілятора: g++ (MinGW/MSYS2) -> clang++ (LLVM) -> cl (MSVC Build Tools).
cd /d "%~dp0"

where g++ >nul 2>nul
if %errorlevel%==0 (
    g++ -std=c++17 -O2 -shared -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -I Models -I DataBase -I Controllers ^
        Models\Tourist.cpp Models\TouristDestination.cpp Models\Attraction.cpp ^
        Models\Museum.cpp Models\Route.cpp Models\TravelPlan.cpp ^
        DataBase\DataLoader.cpp ^
        Controllers\Algorithms.cpp Controllers\TravelSystem.cpp Controllers\c_api.cpp ^
        -o Controllers\travelcore.dll
    goto :done
)

where clang++ >nul 2>nul
if %errorlevel%==0 (
    clang++ -std=c++17 -O2 -shared -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -I Models -I DataBase -I Controllers ^
        Models\Tourist.cpp Models\TouristDestination.cpp Models\Attraction.cpp ^
        Models\Museum.cpp Models\Route.cpp Models\TravelPlan.cpp ^
        DataBase\DataLoader.cpp ^
        Controllers\Algorithms.cpp Controllers\TravelSystem.cpp Controllers\c_api.cpp ^
        -o Controllers\travelcore.dll
    goto :done
)

REM Fallback: MSVC (Visual Studio Build Tools) через vcvarsall + cl /LD
for %%V in ("C:\Program Files\Microsoft Visual Studio\2022\BuildTools" "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools" "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools") do (
    if exist "%%~V\vc\Auxiliary\Build\vcvarsall.bat" (
        call "%%~V\vc\Auxiliary\Build\vcvarsall.bat" x64 >nul
        cl /nologo /std:c++17 /O2 /EHsc /LD /D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH /I Models /I DataBase /I Controllers ^
            Models\Tourist.cpp Models\TouristDestination.cpp Models\Attraction.cpp ^
            Models\Museum.cpp Models\Route.cpp Models\TravelPlan.cpp ^
            DataBase\DataLoader.cpp ^
            Controllers\Algorithms.cpp Controllers\TravelSystem.cpp Controllers\c_api.cpp ^
            /Fe:Controllers\travelcore.dll
        goto :done
    )
)

echo Помилка: не знайдено компілятор (g++, clang++ або MSVC Build Tools).
exit /b 1

:done
if %errorlevel%==0 (
    echo Готово: Controllers\travelcore.dll
) else (
    echo Помилка збірки.
    exit /b 1
)
