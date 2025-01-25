@echo off
setlocal enabledelayedexpansion
set /a count=0
:check
powershell -Command "try { $response = Invoke-WebRequest -Uri http://127.0.0.1:9001 -UseBasicParsing; exit $response.StatusCode } catch { exit 1 }" > nul 2>&1
if !errorlevel! equ 200 (
    echo Server is ready
    start "" "http://127.0.0.1:9001"
    exit /b 0
)
set /a count+=1
if !count! geq 60 (
    echo Server failed to start
    exit /b 1
)
timeout /t 1 /nobreak > nul
goto check
