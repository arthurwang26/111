# SYSTEM_RULES

This document outlines the strict rules that every developer or AI Agent must follow when developing, modifying, or extending the Elder Care Vision Monitoring System.

## 1. Immutable Core Elements (DO NOT MODIFY)
The following elements must NEVER be modified, regenerated, or overwritten without explicit user permission:
- **Authentication Credentials**: Admin accounts, test accounts, and passwords.
- **Environment Variables**: The `.env` file structure and sensitive contents (e.g., API keys, database URLs).
- **Network Ports**: Backend default port (8000), Frontend default dashboard URL (e.g., localhost:5173 or localhost:3000).
- **API Routes**: Names and paths of existing REST endpoints (e.g., `/api/residents`, `/video/stream`).
- **Database Schema**: The core tables (`Resident`, `Event`, `Camera`, `SystemMetrics`) must not be dropped. Adding new tables/columns is allowed, but dropping or altering core relations is prohibited without discussion.
- **Core AI Pipeline Order**: The base pipeline sequential order must remain: `Detection -> Tracking -> (Face/ReID) -> Identity Manager -> Anomaly Detection`.

## 2. Hardware and GPU Policy
- **Primary Device**: GPU (NVIDIA CUDA) is the primary target for all AI inference (YOLO, ArcFace, future models).
- **Fallback**: All models must support a seamless `fallback_cpu` mode if CUDA is unavailable.
- **Memory Management**: Batching and cache clearing must be considered to prevent VRAM Out-of-Memory (OOM) errors.

## 3. Deployment and Environment Management
- Developers/Agents are prohibited from randomly creating new Python environments or modifying the global machine state outside the designated `setup.bat` scripts.
- The `project_root/scripts/` directory is the single source of truth for deployment automation.

## 4. Agent Check-In Requirement
- Before any coding session or deep refactor, the AI Agent MUST read this `SYSTEM_RULES.md` and the `ARCHITECTURE_LOCK.md` file.

