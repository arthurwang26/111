# [檔案用途：即時影像串流 API] (不需更動)
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..db import get_db
from ..cv.capture import pipeline
from ..cv.processor import processor
import cv2
import asyncio

router = APIRouter(prefix="/video", tags=["Video Stream"])

async def frame_generator(db: Session):
    # Ensure camera is running
    if not pipeline.running:
        pipeline.start()
        
    # Reload residents into cv cache
    processor.refresh_residents(db)

    try:
        while True:
            frame = pipeline.get_frame()
            if frame is None:
                await asyncio.sleep(0.1)
                continue
                
            # Process the frame with AI
            processed_frame, names, posture = processor.process_frame(frame, db)
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            # Yield as multipart stream
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
            # Limit framerate
            await asyncio.sleep(1/30) # ~30 FPS max
            
    except asyncio.CancelledError:
        # Client disconnected
        pass

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
