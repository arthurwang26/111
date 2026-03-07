from datetime import datetime
from sqlalchemy.orm import Session
from ..db import Event, Elder
from ..services.line_notify import send_line_alert
import os
import cv2

class AnomalyEngine:
    def __init__(self):
        self.last_fall_alert = {} # elder_id -> datetime to prevent spam
        
    def check_for_anomalies(self, elder_id: int, name: str, posture: str, frame, db: Session):
        """Run business logic rules on the current frame data."""
        if elder_id is None:
            return
            
        now = datetime.now()
        
        # Rule 1: Fall Detection (Posture is Lying)
        if posture == "Lying":
            last_alert = self.last_fall_alert.get(elder_id)
            if last_alert is None or (now - last_alert).total_seconds() > 60: # 1 min cooldown
                # Create snapshot
                snapshot_filename = f"snapshot_fall_{elder_id}_{now.strftime('%Y%m%d%H%M%S')}.jpg"
                snapshot_path = os.path.join(os.getcwd(), 'snapshots', snapshot_filename)
                
                # Ensure snapshots folder exists
                os.makedirs(os.path.join(os.getcwd(), 'snapshots'), exist_ok=True)
                
                cv2.imwrite(snapshot_path, frame)
                
                # Create Event Record
                new_event = Event(
                    elder_id=elder_id,
                    type="FALL",
                    severity="HIGH",
                    description=f"{name} appears to have fallen or is lying down in an unusual area.",
                    snapshot_path=snapshot_path
                )
                db.add(new_event)
                db.commit()
                
                # Send LINE notification asynchronously (simulated here for simplicity, or called directly if fast enough)
                send_line_alert(new_event.description, snapshot_path)
                
                self.last_fall_alert[elder_id] = now
                
        # Rule 2: Inactivity deviation (would require aggregrating ActivityLogs over time)
        # To be fully implemented in a background task

engine = AnomalyEngine()
