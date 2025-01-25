@echo off
echo Starting Django application...
cd /d "E:\Cline\Appmanager"
call "E:\Cline\Appmanager\venv\Scripts\activate.bat"
set "PYTHONPATH=E:\Cline\Appmanager"
set "DJANGO_SETTINGS_MODULE=appmanager.settings"
echo Environment configured, starting server...
start /B python manage.py runserver 127.0.0.1:9000
timeout /t 3 /nobreak > nul
start http://127.0.0.1:9000
echo Server started and browser opened.
echo Press Ctrl+C to stop the server...
pause > nul