# [檔案用途：首頁儀表板資料 API] (不需更動)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import db as models
from .auth import get_current_user
from .schemas import User

router = APIRouter(prefix="/api", tags=["Dashboard"])

@router.get("/residents", response_model=list) # simplified schema for now
def get_residents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve all monitored residents."""
    residents = db.query(models.Resident).all()
    # Mask embeddings for the frontend to save bandwidth
    return [{"id": r.id, "name": r.name, "created_at": r.created_at, "room": r.room} for r in residents]

@router.get("/residents/{resident_id}")
def get_resident_details(resident_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get detailed info, recent activity logs, and baselines for an resident."""
    resident = db.query(models.Resident).filter(models.Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    recent_events = db.query(models.Event).filter(models.Event.resident_id == resident_id).order_by(models.Event.timestamp.desc()).limit(100).all()
    daily_activities = db.query(models.DailyActivity).filter(models.DailyActivity.resident_id == resident_id).order_by(models.DailyActivity.date.desc()).limit(7).all()
    abnormal_events = db.query(models.AbnormalEvent).filter(models.AbnormalEvent.resident_id == resident_id).order_by(models.AbnormalEvent.timestamp.desc()).limit(50).all()

    return {
        "id": resident.id,
        "name": resident.name,
        "recent_events": recent_events,
        "daily_activities": daily_activities,
        "recent_abnormal_events": abnormal_events
    }

@router.get("/events")
def get_recent_events(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent system-wide abnormal events for the dashboard."""
    events = db.query(models.AbnormalEvent).order_by(models.AbnormalEvent.timestamp.desc()).limit(limit).all()
    return events

@router.patch("/events/{event_id}/resolve")
def resolve_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.AbnormalEvent).filter(models.AbnormalEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.is_resolved = True
    db.commit()
    return {"status": "success", "message": f"Abnormal Event {event_id} resolved"}
