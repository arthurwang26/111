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

    def _should_trigger_alert(self, resident_id: int, alert_type: str, cooldown_seconds: int = 60) -> bool:
        """檢查是否超過冷卻時間，避免頻繁發送相同警報"""
        now = datetime.now()
        key = (resident_id, alert_type)
        last_alert = self.last_alerts.get(key)
        if last_alert is None or (now - last_alert).total_seconds() > cooldown_seconds:
            self.last_alerts[key] = now
            return True
        return False

    def evaluate(self, resident_id: int, name: str, posture: str, object_interaction: str, frame, db: Session):
        """
        每一幀都會呼叫這裡。
        您可以根據 posture (姿勢), object_interaction (物件) 與歷史資料寫判斷邏輯。
        """
        if resident_id is None:
            return

        now = datetime.now()
        
        # 🟢 Rule 1: 跌倒偵測 (Level 3 - 最高級別)
        if posture == "Lying":
            if self._should_trigger_alert(resident_id, "fall", cooldown_seconds=60):
                self._trigger_event(
                    db=db,
                    resident_id=resident_id,
                    level=3,
                    event_type="fall",
                    description=f"🚨 [緊急] 偵測到 {name} 有跌倒或不正常倒臥情況！",
                    frame=frame
                )

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
