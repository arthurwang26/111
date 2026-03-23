@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ===================================================
echo   Elder Care Vision Monitoring System (V3)
echo   系統啟動腳本 (Start System)
echo ===================================================

:: 檢查 GPU
echo [*] 正在檢查硬體加速支援...
where nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=2 delims=:" %%a in ('nvidia-smi -q ^| findstr /c:"Product Name"') do (
        set "gpuname=%%a"
        echo [INFO] AI 引擎將嘗試使用 GPU: !gpuname!
        goto break_gpu
    )
    :break_gpu
    echo. >nul
) else (
    echo [!] 未偵測到 NVIDIA GPU, 系統將以 CPU 降級模式運行.
)

:: 啟動後端
echo.
echo [*] 啟動後端 API 伺服器 (FastAPI, Port: 8000)...
start "Elder Care Backend" cmd /k "call venv\Scripts\activate.bat && cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 啟動前端
echo [*] 啟動前端儀表板 (React+Vite, Port: 5173)...
start "Elder Care Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   系統啟動中...
echo   後端 API 文件: http://localhost:8000/docs
echo   前端儀表板:   http://localhost:5173
echo ===================================================
echo   如需關閉系統, 請直接關閉彈出的命令提示字元視窗.
echo ===================================================
pause
