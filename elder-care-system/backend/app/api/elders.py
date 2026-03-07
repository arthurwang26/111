# [檔案用途：長者資料管理(CRUD) API] (不需更動)
"""
長者管理 API
- GET    /api/elders           查詢所有長者
- POST   /api/elders           新增長者（含臉部照片上傳 → embedding 提取）
- GET    /api/elders/{id}      查詢單一長者完整資料
- PUT    /api/elders/{id}      更新長者基本資料
- DELETE /api/elders/{id}      刪除長者
"""

import io
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..db import get_db
from .. import db as models
from .auth import get_current_user

router = APIRouter(prefix="/api/elders", tags=["Elders"])


def _extract_embedding_from_image(image_bytes: bytes) -> list:
    """從上傳的照片提取 512 維 face embedding（使用 FaceLandmarker）。"""
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
        import os

        FACE_MODEL = r"C:\elder_care_models\face_landmarker.task"

        face_opts = mp_python.BaseOptions(model_asset_path=FACE_MODEL)
        face_options = mp_vision.FaceLandmarkerOptions(
            base_options=face_opts,
            running_mode=VisionTaskRunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.3,
        )
        detector = mp_vision.FaceLandmarker.create_from_options(face_options)

        arr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = detector.detect(mp_image)
        if not result.face_landmarks:
            return []

        pts = np.array([[lm.x, lm.y, lm.z] for lm in result.face_landmarks[0]])
        flat = pts.flatten()
        if len(flat) >= 512:
            emb = flat[:512]
        else:
            emb = np.pad(flat, (0, 512 - len(flat)), "constant")

        # Normalize
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm

        return emb.tolist()
    except Exception as e:
        print(f"[Embedding] 提取失敗: {e}")
        return []


@router.get("")
def list_elders(db: Session = Depends(get_db), _=Depends(get_current_user)):
    elders = db.query(models.Elder).all()
    return [{"id": e.id, "name": e.name, "created_at": e.created_at, "has_embedding": bool(e.face_embedding)} for e in elders]


@router.post("")
def create_elder(
    name: str = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    # 確認名字不重複
    existing = db.query(models.Elder).filter(models.Elder.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="此長者姓名已存在")

    embedding = []
    if photo:
        image_bytes = photo.file.read()
        embedding = _extract_embedding_from_image(image_bytes)
        if not embedding:
            raise HTTPException(status_code=422, detail="無法從照片中偵測到臉部，請換一張正面清晰的照片")

    elder = models.Elder(name=name, face_embedding=embedding if embedding else None)
    db.add(elder)
    db.commit()
    db.refresh(elder)

    # 刷新 CV 處理器的長者快取
    try:
        from ..cv.processor import processor
        processor.refresh_elders(db)
    except Exception:
        pass

    return {"id": elder.id, "name": elder.name, "embedding_extracted": bool(embedding)}


@router.get("/{elder_id}")
def get_elder(elder_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    elder = db.query(models.Elder).filter(models.Elder.id == elder_id).first()
    if not elder:
        raise HTTPException(status_code=404, detail="找不到此長者")

    recent_logs = (db.query(models.ActivityLog)
                   .filter(models.ActivityLog.elder_id == elder_id)
                   .order_by(models.ActivityLog.timestamp.desc())
                   .limit(100).all())
    recent_events = (db.query(models.Event)
                     .filter(models.Event.elder_id == elder_id)
                     .order_by(models.Event.timestamp.desc())
                     .limit(20).all())
    baselines = (db.query(models.Baseline)
                 .filter(models.Baseline.elder_id == elder_id)
                 .order_by(models.Baseline.date.desc())
                 .limit(7).all())

    return {
        "id": elder.id,
        "name": elder.name,
        "created_at": elder.created_at,
        "has_embedding": bool(elder.face_embedding),
        "recent_logs": [{"id": l.id, "timestamp": l.timestamp, "activity_level": l.activity_level, "posture": l.posture} for l in recent_logs],
        "recent_events": [{"id": e.id, "timestamp": e.timestamp, "type": e.type, "severity": e.severity, "description": e.description} for e in recent_events],
        "baselines": [{"date": b.date, "avg_activity": b.avg_activity_level} for b in baselines],
    }


@router.put("/{elder_id}")
def update_elder(
    elder_id: int,
    name: str = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    elder = db.query(models.Elder).filter(models.Elder.id == elder_id).first()
    if not elder:
        raise HTTPException(status_code=404, detail="找不到此長者")

    elder.name = name
    if photo:
        image_bytes = photo.file.read()
        embedding = _extract_embedding_from_image(image_bytes)
        if embedding:
            elder.face_embedding = embedding

    db.commit()
    return {"id": elder.id, "name": elder.name}


@router.delete("/{elder_id}")
def delete_elder(elder_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    elder = db.query(models.Elder).filter(models.Elder.id == elder_id).first()
    if not elder:
        raise HTTPException(status_code=404, detail="找不到此長者")
    db.delete(elder)
    db.commit()
    return {"message": f"長者 {elder.name} 已刪除"}
