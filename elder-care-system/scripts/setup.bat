@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ===================================================
echo   Elder Care Vision Monitoring System (V3)
echo   安裝與初始化腳本 (Setup System)
echo ===================================================

:: 1. 環境檢查
echo [*] 執行環境檢查...
call scripts\check_env.bat

:: 2. 建立 Python 虛擬環境
echo.
echo [*] 準備 Python 虛擬環境...
if not exist "venv\" (
    echo [INFO] 正在建立虛擬環境...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] 建立虛擬環境失敗!
        pause
        exit /b 1
    )
    echo [OK] 虛擬環境建立成功.
) else (
    echo [OK] 虛擬環境已存在, 跳過建立.
)

:: 3. 安裝後端套件
echo.
echo [*] 安裝後端 Python 套件...
call venv\Scripts\activate.bat
pip install -r backend\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 後端套件安裝失敗!
    pause
    exit /b 1
)
echo [OK] 後端套件安裝完成.

:: 4. 安裝前端套件
echo.
echo [*] 安裝前端 Node.js 套件...
cd frontend
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 前端 npm 套件安裝失敗!
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] 前端套件安裝完成.

:: 5. 設定環境變數檔
echo.
echo [*] 檢查環境變數設定...
if not exist "backend\.env" (
    echo [INFO] 發現缺少 backend\.env, 將從 backend\.env.example 複製...
    copy backend\.env.example backend\.env
    echo [OK] 已建立 backend\.env, 請記得視需要修改裡面的金鑰.
) else (
    echo [OK] backend\.env 檔案已存在, 跳過複製.
)

echo.
echo ===================================================
echo   安裝程序全部完成! 
echo   現在您可以執行 scripts\start_system.bat 啟動系統
echo ===================================================
pause
