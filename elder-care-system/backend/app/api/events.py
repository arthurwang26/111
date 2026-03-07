# [檔案用途：事件查詢 API] (不需更動)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..db import get_db, AbnormalEvent, DailyActivity, Resident
from .auth import get_current_user

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("/abnormal")
def get_abnormal_events(limit: int = 50, db: Session = Depends(get_db), _=Depends(get_current_user)):
    events = db.query(AbnormalEvent).order_by(desc(AbnormalEvent.timestamp)).limit(limit).all()
    res = []
    for e in events:
        resident = db.query(Resident).filter(Resident.id == e.resident_id).first()
        res.append({
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "resident_name": resident.name if resident else "Unknown",
            "type": e.type,
            "level": e.level,
            "description": e.description,
            "snapshot_path": e.snapshot_path
        })
    return res

@router.get("/daily")
def get_daily_activities(limit: int = 50, db: Session = Depends(get_db), _=Depends(get_current_user)):
    activities = db.query(DailyActivity).order_by(desc(DailyActivity.date)).limit(limit).all()
    res = []
    for a in activities:
        resident = db.query(Resident).filter(Resident.id == a.resident_id).first()
        res.append({
            "id": a.id,
            "date": a.date.isoformat(),
            "resident_name": resident.name if resident else "Unknown",
            "summary": a.ai_summary
        })
    return res
