@echo off
chcp 65001 >nul
REM Запуск smoke-тестів ядра C++ (Tests\.build\smoke_test.exe).
REM Тест не читає JSON-файл бази (C++ ядро не парсить JSON): демо-дані задані
REM у коді тесту, а JSON-бази (Tests\sample_db.json, DataBase\travel_db.json)
REM перевіряються Python-режимом: python Main.py --console Tests\sample_db.json
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
    if not exist Tests\.build\smoke_test.exe (
        echo Не знайдено Tests\.build\smoke_test.exe — збираю автоматично...
        call build.bat --tests
        if %errorlevel% neq 0 (
            echo Помилка збірки.
            exit /b 1
        )
    )
)

echo === Запуск smoke-тесту ===
echo.
Tests\.build\smoke_test.exe
set "RC=%errorlevel%"
echo.
if %RC%==0 (
    echo Тести пройдено успішно (код %RC%).
) else (
    echo Тести завершилися з кодом %RC%.
)
exit /b %RC%
