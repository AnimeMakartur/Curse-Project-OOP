@echo off
chcp 65001 >nul
REM Запуск smoke-тестів ядра C++ (Tests\.build\smoke_test.exe).
REM Використання:
REM   test.bat                  — запуск тестів на демо-базі Tests\sample_db.json
REM   test.bat <файл_бд.json>   — запуск тестів на вказаній базі
REM   test.bat --build          — спочатку перезібрати (build.bat --tests), потім тести
REM   test.bat --build <бд.json>— перезібрати і запустити на вказаній базі
cd /d "%~dp0"

set "DB=Tests\sample_db.json"
set "NEED_BUILD=0"

:parse_args
if /i "%~1"=="" goto :args_done
if /i "%~1"=="--build" (
    set "NEED_BUILD=1"
) else (
    set "DB=%~1"
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
    if not exist Tests\.build\smoke_test.exe (
        echo Не знайдено Tests\.build\smoke_test.exe — збираю автоматично...
        call build.bat --tests
        if %errorlevel% neq 0 (
            echo Помилка збірки.
            exit /b 1
        )
    )
)

if not exist "%DB%" (
    echo Помилка: файл бази "%DB%" не знайдено.
    exit /b 1
)

echo === Запуск smoke-тесту ===
echo База: %DB%
echo.
Tests\.build\smoke_test.exe "%DB%"
set "RC=%errorlevel%"
echo.
if %RC%==0 (
    echo Тести пройдено успішно (код %RC%).
) else (
    echo Тести завершилися з кодом %RC%.
)
exit /b %RC%
