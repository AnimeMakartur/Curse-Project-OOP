@echo off
chcp 65001 >nul
REM Запуск тестів: C++ юніт-тест ядра (Tests\.build\core_test.exe) + Python smoke-тест.
REM Python smoke-тест йде через C++ ядро (ctypes): база Tests\sample_db.json парситься
REM стандартним модулем json у Python, а C++ отримує готові сутності через C API.
REM Використання:
REM   test.bat                  — запуск тестів
REM   test.bat --build          — спочатку перезібрати (build.bat --tests), потім тести
cd /d "%~dp0"

set "NEED_BUILD=0"

:parse_args
if /i "%~1"=="" goto :args_done
if /i "%~1"=="--build" (
    set "NEED_BUILD=1"
)
shift
goto :parse_args

:args_done

if %NEED_BUILD%==1 (
    echo === Збірка (build.bat --tests) ===
    call build.bat --tests
    if %errorlevel% neq 0 (
        echo Помилка збірки.
        exit /b 1
    )
) else (
    if not exist Controllers\travelcore.dll (
        if not exist Controllers\libtravelcore.so (
            if not exist Tests\.build\core_test.exe (
                echo Не знайдено зібране ядро — збираю автоматично...
                call build.bat --tests
                if %errorlevel% neq 0 (
                    echo Помилка збірки.
                    exit /b 1
                )
            )
        )
    )
)

set "RC=0"

echo === C++ юніт-тести ядра ===
echo.
if exist Tests\.build\core_test.exe (
    Tests\.build\core_test.exe
    set "RC=%errorlevel%"
) else (
    echo (core_test.exe не знайдено — пропускаємо)
)

echo.
echo === Python smoke-тест (ctypes -> C++ ядро) ===
echo.
python Tests\smoke_test.py Tests\sample_db.json
if %errorlevel% neq 0 set "RC=%errorlevel%"

echo.
if %RC%==0 (
    echo Тести пройдено успішно (код %RC%).
) else (
    echo Тести завершилися з кодом %RC%.
)
exit /b %RC%
