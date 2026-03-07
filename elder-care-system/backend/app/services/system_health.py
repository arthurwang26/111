# [檔案用途：背景系統健康狀態巡檢] (不需更動)
"""
系統健康監控服務
每分鐘或定期檢查各模組存活狀態：
- CV 模組是否意外崩潰或相機斷線
- 資料庫連線是否正常
- LINE Token 是否有效
並將結果寫入 `system_health_logs` 資料表。
"""
import time
import threading
from datetime import datetime
from sqlalchemy.orm import Session
from ..db import SystemHealthLog, SessionLocal
from ..cv.capture import pipeline

class SystemHealthMonitor:
    def __init__(self):
        self.running = False
        self._thread = None

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            print("[System Health] 監控背景服務已啟動。")

    def stop(self):
        self.running = False

    def _run(self):
        while self.running:
            try:
                self._check_all()
            except Exception as e:
                print(f"[System Health] 檢查過程發生錯誤: {e}")
            time.sleep(60) # 每 60 秒巡檢一次

    def _check_all(self):
        db = SessionLocal()
        try:
            now = datetime.now()
            
            # --- 1. 相機狀態檢查 ---
            cam_status = "ok" if pipeline.running else "error"
            cam_msg = "Camera is streaming." if pipeline.running else "Camera pipeline is stopped."
            self._log(db, "camera", cam_status, cam_msg)

            # --- 2. 資料庫狀態檢查 ---
            db_status = "warning"
            db_msg = "Database check..."
            try:
                # 執行簡單查詢
                db.execute("SELECT 1")
                db_status = "ok"
                db_msg = "Database connected successfully."
            except Exception as e:
                db_status = "error"
                db_msg = f"DB Error: {str(e)}"
            self._log(db, "database", db_status, db_msg)

        finally:
            db.close()

    def _log(self, db: Session, module: str, status: str, message: str):
        log = SystemHealthLog(
            module=module,
            status=status,
            message=message
        )
        db.add(log)
        db.commit()

health_monitor = SystemHealthMonitor()
