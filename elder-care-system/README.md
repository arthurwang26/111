# Elderly Long-term Care Visual Anomaly Detection System

A complete, privacy-focused, real-time visual monitoring system for elderly care using MediaPipe, FastAPI, React, and LINE Messaging API.

## Features
- **Real-time Posture & Face Detection**: Uses MediaPipe for rapid local ML inference.
- **Anomaly Detection Rules**: Detects falls (sudden laying posture) and abnormal inactivity.
- **LINE Notifications**: Instantly pushes alerts with snapshots to caregivers.
- **Privacy First**: All calculations are done locally; only anomaly events are transmitted.
- **Modern Dashboard**: React + Vite + Tailwind CSS dashboard with a dark mode aesthetic.
- **Local SQLite DB**: Zero-configuration needed for edge deployment (e.g. Raspberry Pi).

## Prerequisites
- Docker & Docker Compose
- A standard USB Webcam attached to the host machine
- LINE Channel Access Token (Optional, for notifications)

## 🚀 快速開始 (Quick Start)

### 1. 獲取程式碼與環境
- **團隊協作**：請參考 [遷錄至新電腦指南 (Migration Guide)](C:\Users\arthu\.gemini\antigravity\brain\ca53e959-13a4-4be4-839f-2c48f24d0cdf\migration_guide.md)
- **環境要求**：推薦使用 **Docker Desktop**。

### 2. 下載 AI 模型
在啟動前，請確保已下載 MediaPipe 模型：
```powershell
cd backend
python download_models.py
```
*預設會存放於 `C:\elder_care_models` (Windows) 或 `/app/models` (Docker)。*

### 3. 一鍵啟動 (Docker)
```bash
docker-compose up --build
```
- **Dashboard**: `http://localhost:5173`
- **帳號/密碼**: `admin` / `123456`

---

## 🏗️ 系統架構與開發
有關系統組件、資料流以及如何修改功能的詳細說明，請參閱：
👉 **[系統架構與開發指南 (Architecture Guide)](C:\Users\arthu\.gemini\antigravity\brain\ca53e959-13a4-4be4-839f-2c48f24d0cdf\system_architecture.md)**

---

## 🛠️ 開發人員快速指引
- **修改 UI**: `frontend/src/pages/`
- **調整 AI 規則**: `backend/app/cv/processor.py`
- **增加 API**: `backend/app/api/`
