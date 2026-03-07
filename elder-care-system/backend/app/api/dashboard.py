# [檔案用途：首頁儀表板資料 API] (不需更動)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import db as models
from .auth import get_current_user
from .schemas import User

router = APIRouter(prefix="/api", tags=["Dashboard"])

@router.get("/elders", response_model=list) # simplified schema for now
def get_elders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve all monitored elders."""
    elders = db.query(models.Elder).all()
    # Mask embeddings for the frontend to save bandwidth
    return [{"id": e.id, "name": e.name, "created_at": e.created_at} for e in elders]

@router.get("/elders/{elder_id}")
def get_elder_details(elder_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get detailed info, recent activity logs, and baselines for an elder."""
    elder = db.query(models.Elder).filter(models.Elder.id == elder_id).first()
    if not elder:
        raise HTTPException(status_code=404, detail="Elder not found")
    
    recent_logs = db.query(models.ActivityLog).filter(models.ActivityLog.elder_id == elder_id).order_by(models.ActivityLog.timestamp.desc()).limit(100).all()
    baselines = db.query(models.Baseline).filter(models.Baseline.elder_id == elder_id).order_by(models.Baseline.date.desc()).limit(7).all()
    events = db.query(models.Event).filter(models.Event.elder_id == elder_id).order_by(models.Event.timestamp.desc()).limit(50).all()

    return {
        "id": elder.id,
        "name": elder.name,
        "recent_logs": recent_logs,
        "baselines": baselines,
        "recent_events": events
    }

@router.get("/events")
def get_recent_events(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent system-wide anomaly events for the dashboard."""
    events = db.query(models.Event).order_by(models.Event.timestamp.desc()).limit(limit).all()
    # 返回包括 is_resolved 狀態
    return events

@router.patch("/events/{event_id}/resolve")
def resolve_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.is_resolved = 1
    db.commit()
    return {"status": "success", "message": f"Event {event_id} resolved"}
