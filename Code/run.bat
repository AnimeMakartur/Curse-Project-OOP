@echo off
chcp 65001 >nul
REM Запуск додатку TravelSystem (GUI на PyQt6 поверх C++ ядра travelcore.dll).
REM Програма стартує з головної точки входу Code\Main.py.
REM Використання:
REM   run.bat                          — GUI з базою за замовчуванням (DataBase\travel_db.json)
REM   run.bat <файл_бд.json>           — GUI з вказаною базою
REM   run.bat --console [бд.json]      — консольний режим (без вікна)
REM   run.bat --build [args...]        — спочатку перезібрати DLL (build.bat), потім запуск
cd /d "%~dp0"

set "NEED_BUILD=0"
set "ARGS="

:parse_args
if /i "%~1"=="" goto :args_done
if /i "%~1"=="--build" (
    set "NEED_BUILD=1"
) else (
    set "ARGS=%ARGS% "%~1""
)
shift
goto :parse_args

:args_done

if %NEED_BUILD%==1 (
    echo === Збірка ядра (build.bat) ===
    call build.bat
    if %errorlevel% neq 0 (
        echo Помилка збірки.
        exit /b 1
    )
) else (
    if not exist Controllers\travelcore.dll (
        echo Не знайдено Controllers\travelcore.dll — збираю автоматично...
        call build.bat
        if %errorlevel% neq 0 (
            echo Помилка збірки.
            exit /b 1
        )
    )
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Помилка: не знайдено python у PATH.
    exit /b 1
)

python -c "import PyQt6" >nul 2>nul
if %errorlevel% neq 0 (
    echo Помилка: не встановлено PyQt6. Встановіть: pip install PyQt6
    exit /b 1
)

echo === Запуск TravelSystem ===
python Main.py %ARGS%
exit /b %errorlevel%
