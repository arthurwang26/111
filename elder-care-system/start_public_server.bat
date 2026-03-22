@echo off
setlocal

:: Set UTF-8 for better character handling
chcp 65001 >nul

echo ========================================================
echo   Elder Care System V2 Public Server Launcher
echo ========================================================

:: Define Paths
set "ROOT_DIR=%~dp0"
set "FRONTEND_DIR=%~dp0frontend"
set "BACKEND_DIR=%~dp0backend"

:: [1/4] Reading Ngrok configuration
echo [1/4] Checking Ngrok configuration in .env...
set "NGROK_EXE="
set "NGROK_TOKEN="

if exist "%BACKEND_DIR%\.env" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("%BACKEND_DIR%\.env") do (
        if "%%a"=="NGROK_EXE_PATH" set "NGROK_EXE=%%b"
        if "%%a"=="NGROK_AUTHTOKEN" set "NGROK_TOKEN=%%b"
    )
)

:: Auto-detect Ngrok location
if "%NGROK_EXE%"=="" (
    where /q ngrok
    if not errorlevel 1 (
        set "NGROK_EXE=ngrok"
    ) else if exist "%ROOT_DIR%ngrok.exe" (
        set "NGROK_EXE=%ROOT_DIR%ngrok.exe"
    )
)

:: [2/4] Checking Frontend Build
echo.
echo [2/4] Checking Frontend Build...
if not exist "%FRONTEND_DIR%\dist" (
    echo [INFO] No production build found. Building frontend...
    cd /d "%FRONTEND_DIR%"
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Frontend build failed.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Frontend build already exists.
)

:: [3/4] Starting Backend Server
echo.
echo [3/4] Starting Backend Server (FastAPI on Port 8000)...
cd /d "%BACKEND_DIR%"
:: Use cmd /c to ensure it doesn't block
start "Elder Care Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: [4/4] Starting Ngrok Tunnel
echo.
echo [4/4] Starting Ngrok Tunnel...
timeout /t 5 /nobreak >nul

if not "%NGROK_EXE%"=="" (
    if not "%NGROK_TOKEN%"=="" (
        "%NGROK_EXE%" config add-authtoken %NGROK_TOKEN%
    )
    echo Starting Ngrok on port 8000...
    "%NGROK_EXE%" http 8000
) else (
    echo [WARNING] ngrok.exe not found. 
    echo Please install ngrok or set NGROK_EXE_PATH in backend/.env.
    pause
)

echo Done! Server is running.
pause
