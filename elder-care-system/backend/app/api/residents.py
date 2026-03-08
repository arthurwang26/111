# [檔案用途：長者資料管理(CRUD) API] (不需更動)
"""
長者管理 API
- GET    /api/residents           查詢所有長者
- POST   /api/residents           新增長者（含臉部照片上傳 → embedding 提取）
- GET    /api/residents/{id}      查詢單一長者完整資料
- PUT    /api/residents/{id}      更新長者基本資料
- DELETE /api/residents/{id}      刪除長者
"""

import io
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..db import get_db
from .. import db as models
from .auth import get_current_user

from ..cv.face_recognition import face_recognizer

router = APIRouter(prefix="/api/residents", tags=["Residents"])

def _extract_embedding_from_image(image_bytes: bytes) -> list:
    """從上傳的照片提取歸一化後的 face embedding。"""
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
        import os

        FACE_MODEL = r"C:\elder_care_models\face_landmarker.task"
        if not os.path.exists(FACE_MODEL):
            print(f"[Embedding] 模型路徑不存在: {FACE_MODEL}")
            return []

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
            print("[Embedding] 偵測不到臉部")
            return []

        # 使用統一的 FaceRecognizer 進行特徵提取
        emb = face_recognizer.extract_embedding(result.face_landmarks[0])
        return emb.tolist()
    except Exception as e:
        print(f"[Embedding] 提取失敗: {e}")
        return []

@router.get("")
def list_residents(db: Session = Depends(get_db), _=Depends(get_current_user)):
    residents = db.query(models.Resident).all()
    return [{"id": r.id, "name": r.name, "room": r.room, "created_at": r.created_at, "has_embedding": bool(r.face_embedding)} for r in residents]

@router.post("")
def create_resident(
    name: str = Form(...),
    room: str = Form(None),
    family_line_id: str = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    # 確認名字不重複
    existing = db.query(models.Resident).filter(models.Resident.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="此長者姓名已存在")

    embedding = []
    if photo:
        image_bytes = photo.file.read()
        embedding = _extract_embedding_from_image(image_bytes)
        if not embedding:
            raise HTTPException(status_code=422, detail="無法從照片中偵測到臉部，請換一張正面清晰的照片")

    resident = models.Resident(
        name=name, 
        room=room, 
        family_line_id=family_line_id, 
        face_embedding=embedding if embedding else None
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)

    # 刷新 CV 處理器的長者快取
    try:
        from ..cv.processor import processor
        processor.refresh_residents(db)
    except Exception:
        pass

    return {"id": resident.id, "name": resident.name, "embedding_extracted": bool(embedding)}

@router.get("/{resident_id}")
def get_resident(resident_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    resident = db.query(models.Resident).filter(models.Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="找不到此長者")

    recent_events = (db.query(models.Event)
                     .filter(models.Event.resident_id == resident_id)
                     .order_by(models.Event.timestamp.desc())
                     .limit(100).all())
    
    abnormal_events = (db.query(models.AbnormalEvent)
                     .filter(models.AbnormalEvent.resident_id == resident_id)
                     .order_by(models.AbnormalEvent.timestamp.desc())
                     .limit(20).all())
                     
    daily_activities = (db.query(models.DailyActivity)
                 .filter(models.DailyActivity.resident_id == resident_id)
                 .order_by(models.DailyActivity.date.desc())
                 .limit(7).all())

    return {
        "id": resident.id,
        "name": resident.name,
        "room": resident.room,
        "family_line_id": resident.family_line_id,
        "created_at": resident.created_at,
        "has_embedding": bool(resident.face_embedding),
        "recent_events": [{"id": e.id, "timestamp": e.timestamp, "activity_type": e.activity_type, "object_interaction": e.object_interaction} for e in recent_events],
        "abnormal_events": [{"id": e.id, "timestamp": e.timestamp, "type": e.type, "level": e.level, "description": e.description} for e in abnormal_events],
        "daily_activities": [{"date": d.date, "health_score": d.health_score, "walking_mins": d.walking_mins, "sitting_mins": d.sitting_mins, "sleeping_mins": d.sleeping_mins} for d in daily_activities],
    }

@router.put("/{resident_id}")
def update_resident(
    resident_id: int,
    name: str = Form(...),
    room: str = Form(None),
    family_line_id: str = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    resident = db.query(models.Resident).filter(models.Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="找不到此長者")

    resident.name = name
    if room is not None: resident.room = room
    if family_line_id is not None: resident.family_line_id = family_line_id
    
    if photo:
        image_bytes = photo.file.read()
        embedding = _extract_embedding_from_image(image_bytes)
        if embedding:
            resident.face_embedding = embedding

    db.commit()
    return {"id": resident.id, "name": resident.name}

@router.post("/{resident_id}/photo")
def upload_resident_photo(
    resident_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """獨立上傳/更換長者臉部照片端點。"""
    resident = db.query(models.Resident).filter(models.Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="找不到此長者")

    image_bytes = photo.file.read()
    embedding = _extract_embedding_from_image(image_bytes)

    if not embedding:
        raise HTTPException(
            status_code=422,
            detail="無法從照片中偵測到臉部，請換一張正面清晰的照片"
        )

    resident.face_embedding = embedding
    db.commit()

    # 刷新 CV 處理器的長者快取
    try:
        from ..cv.processor import processor
        processor.refresh_residents(db)
    except Exception:
        pass

    return {"success": True, "message": f"{resident.name} 的臉部特徵已成功更新"}

@router.delete("/{resident_id}")
def delete_resident(resident_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    resident = db.query(models.Resident).filter(models.Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="找不到此長者")
    db.delete(resident)
    db.commit()
    return {"message": f"長者 {resident.name} 已刪除"}
