from app.db import SessionLocal
from app.cv.capture import VideoCapturePipeline
from app.cv.processor import processor
import time

db = SessionLocal()
pipeline = VideoCapturePipeline("cam5.avi")
pipeline.start()
time.sleep(2)
frame = pipeline.get_frame()
print("Frame retrieved:", type(frame))
print("Pipeline Status:", pipeline.status)
if frame is not None:
    try:
        processor.process_frame(frame, db)
        print("Processed successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error in processor:", e)
pipeline.stop()
