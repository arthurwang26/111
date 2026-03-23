# ARCHITECTURE_LOCK

This file locks the core architectural decisions of the Elder Care Vision Monitoring System (V3). 

## 1. Standard Folder Structure
All files must be placed according to this standard structure. Do not invent new root-level folders:
```
elder-care-system/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API Endpoints
│   │   ├── core/         # Security, Configurations, Dependencies
│   │   ├── cv/           # AI Vision Pipeline (Detection, Tracking, Identity, Actions)
│   │   ├── db/           # Session models and CRUD operations
│   │   ├── services/     # External integrations (LINE Bot)
├── frontend/             # React/Vite/Tailwind Application
├── models/               # Model weights (.pt, .onnx, .task)
│   ├── pose/
│   ├── face/
│   ├── reid/
├── scripts/              # Automation batch scripts (setup, start, env_check)
├── config/               # System and AI configuration YAMLs
├── data/                 # Local data storage
│   ├── embeddings/
│   ├── logs/
│   ├── events/
├── docs/                 # System, Architecture, and Agent rules
├── .env                  # Environment Variables
├── .gitignore            # Clean git rules
└── README.md
```

## 2. The Core AI Pipeline
The vision pipeline is strictly locked into the following flow sequence:
1. **Detection**: YOLOv8-Pose (CUDA enabled by default) finds bounding boxes and 17 keypoints.
2. **Tracking**: ByteTrack associates bounding boxes across frames using purely Kalman Filter + IoU to maintain a `Track ID`.
3. **Identity Manager**: 
    - **Face Recognition**: SCRFD/RetinaFace -> Alignment -> ArcFace ONNX (512-d).
    - **Person ReID**: OSNet/FastReID for full-body embeddings (Future integration).
    - **Matching Logic**: The Identity Manager fuses Face, Body, and Track continuity to assign a constant `Person ID`.
4. **Action Recognition Engine**: Analyzes sequences of pose keypoints (Future: ST-GCN/LSTM) to detect anomalies (Falls).

## 3. Database Abstraction
- The system currently uses `SQLite`.
- The SQLAlchemy ORM layer must remain strictly abstracted so that pointing `DATABASE_URL` to a `PostgreSQL` instance works without rewriting queries. Hardcoded SQLite-specific PRAGMAs should be isolated or gracefully handled.

## 4. Identity Management Principle
- `Track ID` (from ByteTrack) is transient. It can be lost if a person is occluded.
- `Person ID` (from Identity Manager) is persistent. A person walking behind a pillar and re-emerging will get a new `Track ID`, but the Identity Manager must re-associate them with the correct `Person ID`.
