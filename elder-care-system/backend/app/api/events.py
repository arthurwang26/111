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
@router.delete("/clear_test")
def clear_test_events(db: Session = Depends(get_db)):
    """清除所有測試或未辨識人物的事件"""
    try:
        events_to_delete = db.query(AbnormalEvent).filter(
            (AbnormalEvent.resident_id == None) |
            (AbnormalEvent.description.like("%測試%")) |
            (AbnormalEvent.description.like("%test%"))
        ).all()
        count = len(events_to_delete)
        for e in events_to_delete:
            db.delete(e)
        db.commit()
        return {"message": f"Successfully deleted {count} test events."}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """手動刪除單筆事件"""
    event = db.query(AbnormalEvent).filter(AbnormalEvent.id == event_id).first()
    if event:
        db.delete(event)
        db.commit()
        return {"message": "Deleted"}
    return {"error": "Not found"}

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
