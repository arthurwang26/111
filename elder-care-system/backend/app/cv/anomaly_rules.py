# [檔案用途：異常事件判定規則與閾值] (⭐️負責異常檢測的同學請專注修改此檔案⭐️)
"""
異常判定規則 (V2)
定義各種事件的判斷條件、持續時間與嚴重等級 (Level 1~3)。
Level 1: 輕微 (例如長時間未活動) -> 紀錄
Level 2: 中度 (例如半夜起床徘徊) -> 紀錄 + 通知
Level 3: 嚴重 (例如跌倒) -> 紀錄 + 立即緊急通知 + 截圖
"""
from datetime import datetime
import os
import cv2
from sqlalchemy.orm import Session
from ..db import AbnormalEvent
from ..services.line_notify import send_line_alert
from .capture import pipeline

class AnomalyRulesEngine:
    def __init__(self):
        self.last_alerts = {} # (resident_id, type) -> datetime
        self.fall_states = {} # track_id -> dict {"start_time": dt, "center": (x,y)}

    def _should_trigger_alert(self, resident_id: int, alert_type: str, cooldown_seconds: int = 60) -> bool:
        """檢查是否超過冷卻時間，避免頻繁發送相同警報"""
        now = datetime.now()
        key = (resident_id, alert_type)
        last_alert = self.last_alerts.get(key)
        if last_alert is None or (now - last_alert).total_seconds() > cooldown_seconds:
            self.last_alerts[key] = now
            return True
        return False

    def determine_posture_yolo(self, keypoints_17x3, box) -> str:
        if keypoints_17x3 is None or len(keypoints_17x3) < 17:
            return "Unknown"
        
        x1, y1, x2, y2 = box
        w, h = (x2 - x1), (y2 - y1)
        
        if w > h * 1.2:
            return "Lying"
            
        # COCO Format
        # Shoulders: 5 (Left), 6 (Right)
        # Hips: 11 (Left), 12 (Right)
        ls, rs = keypoints_17x3[5], keypoints_17x3[6]
        lh, rh = keypoints_17x3[11], keypoints_17x3[12]
        
        # Check confidences
        if all(pt[2] > 0.5 for pt in [ls, rs, lh, rh]):
            avg_shoulder_y = (ls[1] + rs[1]) / 2
            avg_hip_y = (lh[1] + rh[1]) / 2
            
            # Simple rule based on absolute pixels (since y is unnormalized)
            head_to_hip = abs(avg_hip_y - avg_shoulder_y)
            if head_to_hip < h * 0.4:
                # Thorax is compressed -> likely sitting or bent over
                return "Sitting"
            else:
                return "Standing"
                
        return "Unknown"

    def evaluate(self, resident_id: int, name: str, posture: str, object_interaction: str, frame, db: Session, track=None):
        """
        每一幀都會呼叫這裡。
        針對 Fall 執行進階驗證：
        1. Bounding box height drop (h < w)
        2. Body horizontal angle (posture == "Lying")
        3. Fall state duration > 3s
        4. Stationary for 10s
        """
        if resident_id is None:
            return

        now = datetime.now()
        
        # 🟢 Rule 1: 進階跌倒偵測 (Level 3 - 最高級別)
        if posture == "Lying" and track is not None:
            tx1, ty1, tx2, ty2 = track.smoothed_bbox
            cx, cy = (tx1 + tx2) / 2, (ty1 + ty2) / 2
            w, h = (tx2 - tx1), (ty2 - ty1)
            
            # 條件1 & 2: 姿態水平且高度突降 (躺姿時寬度大於高度)
            is_dropped = (h < w * 1.2) 
            
            if is_dropped:
                if track.track_id not in self.fall_states:
                    self.fall_states[track.track_id] = {
                        "start_time": now,
                        "center": (cx, cy)
                    }
                else:
                    state = self.fall_states[track.track_id]
                    duration = (now - state["start_time"]).total_seconds()
                    
                    old_cx, old_cy = state["center"]
                    dist = ((cx - old_cx)**2 + (cy - old_cy)**2)**0.5
                    
                    # 條件4: 跌倒後是否未發生顯著移動 (dist < 40 pixels)
                    if dist > 40:
                        # 發生移動（掙扎或爬行），重新計算靜止時間
                        state["start_time"] = now
                        state["center"] = (cx, cy)
                    elif duration >= 2:
                        # 條件3 & 4 同時滿足：持續躺臥 2 秒且未移動 -> 觸發 CRITICAL
                        if self._should_trigger_alert(resident_id, "fall", cooldown_seconds=60):
                            self._trigger_event(
                                db=db,
                                resident_id=resident_id,
                                level=3,
                                event_type="fall",
                                description=f"🚨 [測試] 偵測到 {name} 發生跌倒，且連續 2 秒無移動跡象！",
                                frame=frame
                            )
            else:
                if track.track_id in self.fall_states:
                    del self.fall_states[track.track_id]
        else:
            if track and track.track_id in self.fall_states:
                del self.fall_states[track.track_id]

        # 🟡 Rule 2: 輪椅/危險物品 異常互動 (Level 2 - 中級)
        # 您可以在這裡加入例如: if object_interaction == "knife" 等判斷
        if object_interaction and "dangerous" in object_interaction:
             if self._should_trigger_alert(resident_id, "danger_obj", cooldown_seconds=120):
                self._trigger_event(
                    db=db,
                    resident_id=resident_id,
                    level=2,
                    event_type="dangerous_object",
                    description=f"⚠️ {name} 正在接觸危險物品 ({object_interaction})。",
                    frame=frame
                )
                
        # 🟡 Rule 3: 半夜活動異常 (Level 2 - 中級)
        current_hour = now.hour
        if (current_hour >= 23 or current_hour <= 4) and posture in ["Standing", "Walking"]:
            if self._should_trigger_alert(resident_id, "night_activity", cooldown_seconds=300): # 5mins cooldown
                 self._trigger_event(
                    db=db,
                    resident_id=resident_id,
                    level=2,
                    event_type="night_activity",
                    description=f"⚠️ {name} 在半夜 {current_hour} 點起床活動。",
                    frame=frame
                )

        # 🔵 Rule 4: 長時間未活動 (Level 1)
        # 此功能需要依賴一段時間內的連續數據統計，建議由背景服務或另寫邏輯計算
        pass

    def _trigger_event(self, db: Session, resident_id: int, level: int, event_type: str, description: str, frame):
        """將異常寫入資料庫，並針對 Level 2/3 發出 LINE 警報與後台錄影"""
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M%S')
        
        # 存檔截圖
        snapshot_filename = f"event_{event_type}_{resident_id}_{timestamp}.jpg"
        snapshot_path = os.path.join(os.getcwd(), 'snapshots', snapshot_filename)
        os.makedirs(os.path.join(os.getcwd(), 'snapshots'), exist_ok=True)
        cv2.imwrite(snapshot_path, frame)

        # 啟動後台錄影 (擷取事前與事後影像)
        video_filename = f"event_{event_type}_{resident_id}_{timestamp}.mp4"
        video_path = os.path.join(os.getcwd(), 'snapshots', video_filename)
        if pipeline and pipeline.running:
            pipeline.save_clip_async(video_path, post_event_seconds=10)

        # 寫入資料庫
        new_event = AbnormalEvent(
            resident_id=resident_id,
            type=event_type,
            level=level,
            description=description,
            snapshot_path=snapshot_path,
        )
        db.add(new_event)
        db.commit()

        # 發放通知 (Level 2, 3 發送 LINE)
        if level >= 2:
            send_line_alert(description, image_path=snapshot_path, level=level)

anomaly_engine = AnomalyRulesEngine()
