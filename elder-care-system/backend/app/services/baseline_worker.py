# [檔案用途：長者日常作息基準線背景任務] (處理誤報邏輯可改)
"""
活動基線追蹤引擎
- 每 5 分鐘計算各長者的即時活動水平（目前是否在畫面中移動）
- 每日凌晨 1 點計算 7 天滾動平均，存入 Baseline 資料表
- 偏差 >20% 或靜止 >30 分鐘 → 觸發警報
"""

import threading
import time
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..db import Elder, ActivityLog, Baseline, Event
from .line_notify import send_line_alert


class BaselineWorker:
    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None
        # elder_id → 最後活動時間戳
        self._last_activity: dict[int, datetime] = {}
        # 靜止警報冷卻（避免重複通知）
        self._inactivity_alerted: dict[int, datetime] = {}

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[BaselineWorker] 已啟動")

    def stop(self):
        self._running = False

    def record_activity(self, elder_id: int):
        """由 CV 引擎呼叫，記錄長者有活動的時刻。"""
        self._last_activity[elder_id] = datetime.now()

    def _loop(self):
        last_daily = date.today() - timedelta(days=1)
        while self._running:
            db = SessionLocal()
            try:
                now = datetime.now()

                # ---- 每 5 分鐘計算 ActivityLog ----
                elders = db.query(Elder).all()
                for elder in elders:
                    last = self._last_activity.get(elder.id)
                    # 過去 5 分鐘內有活動 → activity_level=1，否則=0
                    active = 1 if (last and (now - last).total_seconds() < 300) else 0
                    log = ActivityLog(
                        elder_id=elder.id,
                        activity_level=active,
                        posture="Unknown",
                    )
                    db.add(log)

                    # 靜止 >30 分鐘 → 警報
                    if (last and (now - last).total_seconds() > 1800):
                        last_alert = self._inactivity_alerted.get(elder.id)
                        if not last_alert or (now - last_alert).total_seconds() > 3600:
                            msg = (f"⚠️ 靜止警報\n長者 {elder.name} 已超過 30 分鐘沒有活動（最後偵測：{last.strftime('%H:%M')}）")
                            ev = Event(
                                elder_id=elder.id,
                                type="INACTIVITY",
                                severity="MEDIUM",
                                description=msg,
                            )
                            db.add(ev)
                            send_line_alert(msg)
                            self._inactivity_alerted[elder.id] = now

                db.commit()

                # ---- 執行舊資料清理（每天凌晨 2 點） ----
                if now.hour == 2 and now.minute < 5:
                     self._cleanup_old_logs(db)

                # ---- 每日凌晨計算基線（或啟動時補算） ----
                today = date.today()
                if (now.hour == 1 or not last_daily) and today != last_daily:
                    # 檢查最後一筆基線日期
                    last_bl = db.query(Baseline).order_by(Baseline.date.desc()).first()
                    target_date = last_bl.date.date() + timedelta(days=1) if last_bl else (today - timedelta(days=1))
                    
                    while target_date < today:
                        self._compute_daily_baselines(db, target_date)
                        target_date += timedelta(days=1)
                        
                    last_daily = today

            except Exception as e:
                print(f"[BaselineWorker] 錯誤: {e}")
            finally:
                db.close()

            time.sleep(300)  # 每 5 分鐘

    def _cleanup_old_logs(self, db: Session):
        """清理 30 天前的詳細 ActivityLog 以節省空間。"""
        limit_date = datetime.now() - timedelta(days=30)
        deleted = db.query(ActivityLog).filter(ActivityLog.timestamp < limit_date).delete()
        db.commit()
        if deleted > 0:
            print(f"[BaselineWorker] 已清理 {deleted} 筆過期日誌")

    def _compute_daily_baselines(self, db: Session, target_date: date):
        """計算昨日各長者的活動均值，並與 7 天均值比較。"""
        yesterday = target_date - timedelta(days=1)
        elders = db.query(Elder).all()

        for elder in elders:
            # 昨日平均活動量
            logs = (db.query(ActivityLog)
                    .filter(ActivityLog.elder_id == elder.id)
                    .filter(ActivityLog.timestamp >= datetime.combine(yesterday, datetime.min.time()))
                    .filter(ActivityLog.timestamp < datetime.combine(target_date, datetime.min.time()))
                    .all())
            if not logs:
                continue

            avg = sum(l.activity_level or 0 for l in logs) / len(logs)

            # 存入 Baseline
            bl = Baseline(elder_id=elder.id, date=yesterday, avg_activity_level=avg)
            db.add(bl)

            # 與 7 天均值比較
            past_7 = (db.query(Baseline)
                      .filter(Baseline.elder_id == elder.id)
                      .order_by(Baseline.date.desc())
                      .limit(7).all())
            if len(past_7) >= 3:
                mean_7 = sum(b.avg_activity_level for b in past_7) / len(past_7)
                if mean_7 > 0:
                    deviation = abs(avg - mean_7) / mean_7
                    if deviation > 0.20:
                        pct = f"{deviation*100:.0f}%"
                        direction = "高於" if avg > mean_7 else "低於"
                        msg = (f"📊 活動異常警報\n長者 {elder.name} 昨日活動量 {direction}7日均值 {pct}\n"
                               f"（昨日：{avg:.2f}，7日均：{mean_7:.2f}）")
                        ev = Event(
                            elder_id=elder.id,
                            type="ACTIVITY_DEVIATION",
                            severity="MEDIUM",
                            description=msg,
                        )
                        db.add(ev)
                        send_line_alert(msg)

        db.commit()
        print(f"[BaselineWorker] {target_date} 基線計算完成")


# 全域單例
baseline_worker = BaselineWorker()
