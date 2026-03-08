# [檔案用途：首頁儀表板資料 API] (不需更動)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import db as models
from .auth import get_current_user
from .schemas import User

router = APIRouter(prefix="/api", tags=["Dashboard"])


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
