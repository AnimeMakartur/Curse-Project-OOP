@echo off
chcp 65001 >nul
REM Збірка ядра C++ у shared-бібліотеку Controllers\travelcore.dll
REM Порядок пошуку компілятора: g++ (MinGW/MSYS2) -> clang++ (LLVM) -> cl (MSVC Build Tools).
cd /d "%~dp0"

set "SOURCES=Models\Src\City.cpp Models\Src\Lane.cpp Models\Src\PathStep.cpp Models\Src\Tourist.cpp Models\Src\TouristDestination.cpp Models\Src\Attraction.cpp Models\Src\Museum.cpp Models\Src\Route.cpp Models\Src\TravelPlan.cpp Controllers\Src\Algorithms.cpp Controllers\Src\TravelSystem.cpp Controllers\Src\c_api.cpp"

REM -static (g++/clang++) та /MT (cl): лінкуємо libgcc/libstdc++/winpthread ВСЕРЕДИНУ dll,
REM щоб на цільовій машині не бракувало libstdc++-6.dll, libgcc_s_seh-1.dll, libwinpthread-1.dll.
where g++ >nul 2>nul
if %errorlevel%==0 (
    g++ -std=c++17 -O2 -Wall -Wextra -shared -static -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -I Models\Include -I Controllers\Include ^
        %SOURCES% ^
        -o Controllers\travelcore.dll
    goto :done
)

where clang++ >nul 2>nul
if %errorlevel%==0 (
    clang++ -std=c++17 -O2 -Wall -Wextra -shared -static -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -I Models\Include -I Controllers\Include ^
        %SOURCES% ^
        -o Controllers\travelcore.dll
    goto :done
)

REM Fallback: MSVC (Visual Studio Build Tools) через vcvarsall + cl /LD
for %%V in ("C:\Program Files\Microsoft Visual Studio\2022\BuildTools" "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools" "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools") do (
    if exist "%%~V\vc\Auxiliary\Build\vcvarsall.bat" (
        call "%%~V\vc\Auxiliary\Build\vcvarsall.bat" x64 >nul
        cl /nologo /std:c++17 /O2 /W4 /EHsc /LD /MT /D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH /I Models /I Controllers ^
            %SOURCES% ^
            /Fe:Controllers\travelcore.dll
        goto :done
    )
)

echo Помилка: не знайдено компілятор (g++, clang++ або MSVC Build Tools).
exit /b 1

:done
if %errorlevel% neq 0 (
    echo Помилка збірки бібліотеки.
    exit /b 1
)
echo Готово: Controllers\travelcore.dll

if /i "%~1"=="--tests" (
    if not exist Tests\.build mkdir Tests\.build
    where g++ >nul 2>nul && (
        g++ -std=c++17 -O2 -Wall -Wextra -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -I Models\Include -I Controllers\Include ^
            Tests\core_test.cpp %SOURCES% -o Tests\.build\core_test.exe
    ) || (
        clang++ -std=c++17 -O2 -Wall -Wextra -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -I Models\Include -I Controllers\Include ^
            Tests\core_test.cpp %SOURCES% -o Tests\.build\core_test.exe
    )
    if %errorlevel%==0 echo Готово: Tests\.build\core_test.exe
)
exit /b 0
