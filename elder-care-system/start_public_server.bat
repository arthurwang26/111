@echo off
setlocal
echo ========================================================
echo   Elder Care System V2 Public Server Launcher
echo ========================================================

:: 定義路徑
set "FRONTEND_DIR=%~dp0frontend"
set "BACKEND_DIR=%~dp0backend"
set "NGROK_EXE=C:\Users\arthu\Downloads\ngrok-v3-stable-windows-amd64\ngrok.exe"
set "NGROK_AUTH=2x1vZ2F5F2OxDnQWC5ORCZfrD7u_yHm8ya8YaYh2bsa2LDv3"

:: 1. 檢查並編譯前端 (如果 dist 不存在)
echo [1/3] Checking Frontend Build...
if not exist "%FRONTEND_DIR%\dist" (
    echo Building frontend...
    cd "%FRONTEND_DIR%"
    call npm run build
    if %errorlevel% neq 0 (
        echo Error building frontend. Please check your Vite/React setup.
        pause
        exit /b %errorlevel%
    )
    echo Frontend build complete.
) else (
    echo Frontend build already exists in %FRONTEND_DIR%\dist. Skipping build...
)

:: 2. 啟動後端伺服器 (靜態掛載 Frontend)
echo.
echo [2/3] Starting Backend Server (FastAPI on Port 8000)...
cd "%BACKEND_DIR%"
start "Elder Care Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 3. 等待後端啟動
timeout /t 5 /nobreak >nul

:: 4. 啟動 Ngrok
echo.
echo [3/3] Starting Ngrok Tunnel...
if exist "%NGROK_EXE%" (
    echo Configuring Ngrok authentication...
    "%NGROK_EXE%" config add-authtoken %NGROK_AUTH%
    echo Starting Ngrok on port 8000...
    "%NGROK_EXE%" http 8000
) else (
    echo WARNING: ngrok.exe not found at %NGROK_EXE%.
    echo Please install ngrok or check the path.
    pause
)

echo Done! The server should be running publically.
pause
