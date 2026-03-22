# [檔案用途：即時影像串流 API] (不需更動)
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..db import get_db
from ..cv.capture import pipeline
from ..cv.processor import processor
import cv2
import asyncio
import time

router = APIRouter(prefix="/video", tags=["Video Stream"])

async def frame_generator(db: Session):
    # Ensure camera is running
    if not pipeline.running:
        pipeline.start()

    try:
        last_count = -1
        while True:
            result = pipeline.get_encoded_frame()
            if result is None:
                await asyncio.sleep(0.1)
                continue
                
            encoded_frame, current_count = result
            if encoded_frame is not None and current_count > last_count:
                last_count = current_count
                # Yield as multipart stream
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + encoded_frame + b'\r\n')
                   
            # Check faster but only yield on new frame
            await asyncio.sleep(0.02)
            
    except asyncio.CancelledError:
        # Client disconnected
        pass

@router.get("/proxy")
def proxy_stream(source: str, camera_id: int = None):
    """Direct MJPEG proxy without AI processing, preventing pipeline conflicts, and updates camera status."""
    def gen():
        # 如果前端偷偷嘗試透過 proxy 取得主畫面的影像(可能因為放大的 BUG)，強制攔截並提供目前已處理好、有骨架的快取，確保完全不卡頓
        if camera_id is not None and pipeline.active_camera_id == camera_id:
            last_count = -1
            while True:
                result = pipeline.get_encoded_frame()
                if result is not None:
                    encoded_frame, current_count = result
                    if encoded_frame is not None and current_count > last_count:
                        last_count = current_count
                        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + encoded_frame + b'\r\n')
                time.sleep(0.02)
            return

        # Handle webcam indices
        try:
            val = int(source)
        except (ValueError, TypeError):
            val = source
            
        from ..db import SessionLocal, Camera

        if camera_id:
            with SessionLocal() as db_session:
                cam = db_session.query(Camera).filter(Camera.id == camera_id).first()
                if cam and cam.status != "connecting":
                    cam.status = "connecting"
                    db_session.commit()

        cap = cv2.VideoCapture(val)
        try:
            if not cap.isOpened():
                if camera_id:
                    with SessionLocal() as db_session:
                        cam = db_session.query(Camera).filter(Camera.id == camera_id).first()
                        if cam and cam.status != "offline":
                            cam.status = "offline"
                            db_session.commit()
                return

            if camera_id:
                with SessionLocal() as db_session:
                    cam = db_session.query(Camera).filter(Camera.id == camera_id).first()
                    if cam and cam.status != "active":
                        cam.status = "active"
                        db_session.commit()

            while True:
                ret, frame = cap.read()
                if not ret:
                    if camera_id:
                        with SessionLocal() as db_session:
                            cam = db_session.query(Camera).filter(Camera.id == camera_id).first()
                            if cam and cam.status != "offline":
                                cam.status = "offline"
                                db_session.commit()
                    break
                # Resize to save bandwidth for grid views
                frame = cv2.resize(frame, (640, 360))
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                if not ret:
                    continue
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(1/30)
        finally:
            cap.release()

    return StreamingResponse(
        gen(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/stream")
def video_stream(source: str = None, camera_id: int = None, db: Session = Depends(get_db)):
    """MJPEG stream endpoint. Supports 'camera_id' or 'source' to switch camera."""
    target_id = camera_id
    target_source = source

    # 如果只有 source，嘗試查找 camera_id
    if not target_id and target_source:
        from ..db import Camera
        cam = db.query(Camera).filter(Camera.source == target_source).first()
        if cam:
            target_id = cam.id

    # 如果只有 camera_id，查找 source
    if target_id and not target_source:
        from ..db import Camera
        cam = db.query(Camera).filter(Camera.id == target_id).first()
        if cam:
            target_source = cam.source

    if target_source:
        pipeline.update_source(target_source, camera_id=target_id)
        
    return StreamingResponse(
        frame_generator(db),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
