@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py migrate
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py seed_blogs
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py seed_demo
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py runserver
pause
exit /b 0
:error
echo Failed. Check Python installation and internet connection.
pause
exit /b 1
