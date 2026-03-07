from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db, Resident, AbnormalEvent
from ..services.line_notify import send_line_alert
from ..cv.capture import pipeline

router = APIRouter(prefix="/api/test", tags=["Tests"])

@router.post("/line")
def test_line():
    success = send_line_alert("🔔 [系統測試] 這是由 Dashboard 觸發的 LINE 推播測試！", level=1)
    return {"success": success}

@router.post("/fall")
def test_fall(db: Session = Depends(get_db)):
    resident = db.query(Resident).first()
    if not resident:
        return {"success": False, "message": "No residents found"}
    
    event = AbnormalEvent(
        resident_id=resident.id,
        type="fall",
        level=3,
        description=f"🚨 [系統測試] 模擬 {resident.name} 發生跌倒！",
    )
    db.add(event)
    db.commit()
    send_line_alert(event.description, level=3)
    return {"success": True}

@router.post("/snapshot")
def test_snapshot(db: Session = Depends(get_db)):
    import os
    import cv2
    from datetime import datetime
    
    resident = db.query(Resident).first()
    if not resident:
        return {"success": False, "message": "No residents found"}

    frame = pipeline.get_frame()
    if frame is None:
        return {"success": False, "message": "Camera offline"}
        
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    snapshot_filename = f"test_snapshot_{timestamp}.jpg"
    snapshot_path = os.path.join(os.getcwd(), 'snapshots', snapshot_filename)
    os.makedirs(os.path.join(os.getcwd(), 'snapshots'), exist_ok=True)
    cv2.imwrite(snapshot_path, frame)
    
    event = AbnormalEvent(
        resident_id=resident.id,
        type="snapshot",
        level=2,
        description=f"📸 [系統測試] 模擬異常截圖事件",
        snapshot_path=snapshot_path
    )
    db.add(event)
    db.commit()
    send_line_alert(event.description, image_path=snapshot_path, level=2)
    return {"success": True}

@router.get("/health")
def test_health():
    return {"success": True, "message": "API 連線正常！"}
