@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ===================================================
echo   Elder Care Vision Monitoring System (V3)
echo   環境狀態檢查腳本 (Environment Checker)
echo ===================================================
echo.

set HAS_ERROR=0

:: 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [X] Python 未安裝或未加入環境變數 path 中!
    set HAS_ERROR=1
) else (
    echo [OK] Python 已安裝
)

:: 2. Check Node
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [X] NodeJS 未安裝或未加入環境變數 path 中!
    set HAS_ERROR=1
) else (
    echo [OK] NodeJS 已安裝
)

:: 3. Check GPU / CUDA
where nvidia-smi >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] 找不到 nvidia-smi, 系統可能沒有 NVIDIA GPU 或是驅動程式有誤, 將降級為 CPU 運行.
) else (
    for /f "tokens=2 delims=:" %%a in ('nvidia-smi -q ^| findstr /c:"Product Name"') do (
        set "gpuname=%%a"
        echo [OK] GPU Detected! !gpuname!
        goto break_gpu
    )
    :break_gpu
    echo. >nul
)

:: 4. Check Models directory
set MODEL_DIR=C:\elder_care_models
if not exist "%MODEL_DIR%" (
    echo [X] 找不到模型目錄 %MODEL_DIR%. 請確定模型已下載.
    set HAS_ERROR=1
) else (
    echo [OK] 模型目錄存在
    if not exist "%MODEL_DIR%\yolov8n-pose.pt" echo [!] 缺少模型: yolov8n-pose.pt
    if not exist "%MODEL_DIR%\face_landmarker.task" echo [!] 缺少模型: face_landmarker.task
    if not exist "%MODEL_DIR%\buffalo_l\w600k_r50.onnx" echo [!] 缺少模型: w600k_r50.onnx
)

:: 5. Check .env
if not exist "..\backend\.env" (
    echo [X] backend/.env 不存在. 請複製 backend/.env.example 建立一份.
    set HAS_ERROR=1
) else (
    echo [OK] 找到 backend/.env
)

:: 6. Check DB
if not exist "..\backend\elder_care.db" (
    if not exist "..\backend\elder_care_v2.db" (
        echo [!] 資料庫尚未建立，將在後端啟動時自動生成.
    ) else (
         echo [OK] 找到既有資料庫 (elder_care_v2.db)
    )
) else (
    echo [OK] 找到既有資料庫 (elder_care.db)
)

echo.
if %HAS_ERROR% EQU 1 (
    echo [系統狀態] 環境檢查發現錯誤，請先修復上述打 [X] 的項目！
) else (
    echo [系統狀態] 環境檢查完畢，符合基本運行條件。
)
echo ===================================================
pause
