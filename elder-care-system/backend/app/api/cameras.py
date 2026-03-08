# [檔案用途：攝影機管理 API] (不需更動)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, Camera
from .auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

class CameraCreate(BaseModel):
    name: str
    source: str
    location: str = None

class CameraUpdate(BaseModel):
    name: str = None
    source: str = None
    location: str = None
    status: str = None

@router.get("")
def list_cameras(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Camera).all()

@router.post("")
def create_camera(data: CameraCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cam = Camera(name=data.name, source=data.source, location=data.location)
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam

@router.put("/{camera_id}")
def update_camera(camera_id: int, data: CameraUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    if data.name: cam.name = data.name
    if data.source: cam.source = data.source
    if data.location: cam.location = data.location
    if data.status: cam.status = data.status
    db.commit()
    return cam

@router.delete("/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    db.delete(cam)
    db.commit()
    return {"message": "Camera deleted"}

@router.post("/{camera_id}/restart")
def restart_camera(camera_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    from app.cv.capture import pipeline
    if pipeline.active_camera_id == camera_id:
        pipeline.update_source(cam.source, cam.id, force=True)
    return {"message": "Camera restart triggered"}
