@echo off
setlocal
echo ========================================================
echo   Elder Care System V2 Public Server Launcher
echo ========================================================

:: 定義路徑
set "FRONTEND_DIR=%~dp0frontend"
set "BACKEND_DIR=%~dp0backend"

:: [1/4] 從 .env 讀取 Ngrok 設定
echo [1/4] Reading Ngrok configuration from .env...
set "NGROK_EXE="
set "NGROK_TOKEN="

if exist "%BACKEND_DIR%\.env" (
    for /f "tokens=1,2 delims==" %%a in ('findstr /r "^NGROK_EXE_PATH= ^NGROK_AUTHTOKEN=" "%BACKEND_DIR%\.env"') do (
        if "%%a"=="NGROK_EXE_PATH" set "NGROK_EXE=%%b"
        if "%%a"=="NGROK_AUTHTOKEN" set "NGROK_TOKEN=%%b"
    )
)

:: 自動尋找 Ngrok.exe 邏輯
if "%NGROK_EXE%"=="" (
    where /q ngrok
    if %errorlevel% equ 0 (
        set "NGROK_EXE=ngrok"
    ) else if exist "%~dp0ngrok.exe" (
        set "NGROK_EXE=%~dp0ngrok.exe"
    )
)

:: 2. 檢查並編譯前端 (如果 dist 不存在)
echo.
echo [2/4] Checking Frontend Build...
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

:: 3. 啟動後端伺服器 (靜態掛載 Frontend)
echo.
echo [3/4] Starting Backend Server (FastAPI on Port 8000)...
cd "%BACKEND_DIR%"
start "Elder Care Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 4. 等待後端啟動
timeout /t 5 /nobreak >nul

:: 5. 啟動 Ngrok
echo.
echo [4/4] Starting Ngrok Tunnel...
if not "%NGROK_EXE%"=="" (
    if not "%NGROK_TOKEN%"=="" (
        echo Configuring Ngrok authentication...
        "%NGROK_EXE%" config add-authtoken %NGROK_TOKEN%
    )
    echo Starting Ngrok on port 8000...
    "%NGROK_EXE%" http 8000
) else (
    echo WARNING: ngrok.exe not found. 
    echo Please install ngrok, set it in backend/.env, or place it in the project root.
    pause
)

echo Done! The server should be running publically.
pause
