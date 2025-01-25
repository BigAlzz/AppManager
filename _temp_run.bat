@echo off
setlocal enabledelayedexpansion
title Django Server - Appmanager
cd /d "E:\Cline\Appmanager"
echo Starting Django application...
echo Project root: %CD%
echo Activating virtual environment...
if exist "E:\Cline\Appmanager\venv\Scripts\activate.bat" (
    call "E:\Cline\Appmanager\venv\Scripts\activate.bat" & (
        if !errorlevel! neq 0 (
            echo Failed to activate virtual environment
            exit /b 1
        ) else (
            echo Virtual environment activated successfully
            echo Using Python: & where python
        )
    )
) else (
    echo Virtual environment activation script not found
    exit /b 1
)
echo Setting up Django environment...
echo Using settings module: Appmanager.settings
set "DJANGO_SETTINGS_MODULE=Appmanager.settings"
set "PYTHONUNBUFFERED=1"
set "DJANGO_CORS_HEADERS_ALLOW_ALL=1"
set "DJANGO_CORS_ORIGIN_ALLOW_ALL=1"
set "DJANGO_CORS_ALLOW_CREDENTIALS=1"
set "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1"
echo Starting Django server...
start "" cmd /c "E:\Cline\Appmanager\_temp_health.bat"
echo Server starting at http://127.0.0.1:9001
echo Command: python manage.py runserver...
python manage.py runserver 127.0.0.1:9001 --noreload --insecure