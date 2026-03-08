import cv2
import threading
import time
import os
import collections
from dotenv import load_dotenv

# 讀取環境變數
load_dotenv()

class VideoCapturePipeline:
    def __init__(self, source=0, buffer_seconds=10, fps=30):
        # 嘗試從環境變數讀取 CAMERA_SOURCE
        env_source = os.getenv("CAMERA_SOURCE", source)
        try:
            self.source = int(env_source)
        except (ValueError, TypeError):
            self.source = env_source
            
        self.target_source = self.source
        self.active_camera_id = None
        self._last_synced_status = None
        self.cap = None
        self.running = False
        self.current_frame = None
        self.lock = threading.Lock()
        
        # Ring buffer for pre-event frames
        self.buffer_size = buffer_seconds * fps
        self.frame_buffer = collections.deque(maxlen=self.buffer_size)
        self.fps = fps
        self.status = "offline"
        
        print(f"[Capture] 影像管理啟動，初始來源: {self.source}")
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        if self.cap:
            self.cap.release()

    def _update_db_status(self, status: str):
        """將狀態同步回資料庫 (僅當 active_camera_id 存在且狀態改變時)"""
        if self.active_camera_id is None:
            return
        
        # 增加本地快取判斷，避免頻繁寫入 SQLite 導致鎖定
        if self._last_synced_status == status:
            return

        try:
            from ..db import SessionLocal, Camera
            with SessionLocal() as db:
                cam = db.query(Camera).filter(Camera.id == self.active_camera_id).first()
                if cam:
                    # 再次確認 DB 裡的狀態是否真的不同
                    if cam.status != status:
                        cam.status = status
                        db.commit()
                        print(f"[Capture] 資料庫狀態同步成功: Camera {self.active_camera_id} -> {status}")
                    self._last_synced_status = status
        except Exception as e:
            # 針對 SQLite 繁忙情況做靜默處理或記錄
            print(f"[Capture] 資料庫同步警告 (常發於 SQLite 鎖定): {e}")
            
    def _capture_loop(self):
        while self.running:
            # 1. 檢查是否需要切換來源
            if self.cap is None or self.source != self.target_source:
                if self.cap:
                    self.cap.release()
                
                self.source = self.target_source
                print(f"[Capture] 正在連線至來源: {self.source} ...")
                self.status = "connecting"
                self._update_db_status("connecting")
                self.cap = cv2.VideoCapture(self.source)
                
                if not self.cap.isOpened():
                    print(f"[Capture] 連線失敗: {self.source}")
                    self.status = "offline"
                    self._update_db_status("offline")
                    time.sleep(5) 
                    continue
                else:
                    print(f"[Capture] 連線成功: {self.source}")
                    # 使用 'active' 以配合前端樣式
                    self.status = "active" 
                    self._update_db_status("active")

            # 2. 正常讀取幀
            ret, frame = self.cap.read()
            if not ret:
                print(f"[Capture] 影像讀取中斷: {self.source}，嘗試重新連線...")
                self.status = "offline"
                self._update_db_status("offline")
                self.cap.release()
                self.cap = None
                time.sleep(2)
                continue
                
            self.status = "active"
            with self.lock:
                self.current_frame = frame
                self.frame_buffer.append(frame.copy())
                
    def update_source(self, new_source, camera_id: int = None):
        # Normalize new_source
        try:
            val = int(new_source)
        except (ValueError, TypeError):
            val = new_source
            
        with self.lock:
            # 即使 source 相同，如果 camera_id 不同也要更新，以便同步狀態
            if self.target_source == val and self.active_camera_id == camera_id:
                return
            print(f"[Capture] 安排切換來源: {self.target_source} (ID:{self.active_camera_id}) -> {val} (ID:{camera_id})")
            self.target_source = val
            self.active_camera_id = camera_id
            self.current_frame = None
            self.frame_buffer.clear()

    def get_frame(self):
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def save_clip_async(self, filepath: str, post_event_seconds: int = 10):
        """
        異步儲存「事件發生前 N 秒 + 發生後 N 秒」的影片。
        """
        def _record():
            # 1. 取得事發前的緩衝區影像
            with self.lock:
                pre_frames = list(self.frame_buffer)
                
            # 2. 收集事發後的影像
            post_frames = []
            target_post_frames = post_event_seconds * self.fps
            
            for _ in range(target_post_frames):
                frame = self.get_frame()
                if frame is not None:
                    post_frames.append(frame)
                time.sleep(1.0 / self.fps)
                
            all_frames = pre_frames + post_frames
            if not all_frames:
                return
                
            # 3. 寫入 MP4
            try:
                h, w = all_frames[0].shape[:2]
                # 'mp4v' 在 Windows 上通常比 'avc1' 穩定
                fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                out = cv2.VideoWriter(filepath, fourcc, self.fps, (w, h))
                
                if not out.isOpened():
                    print(f"[Capture] Error: 無法建立 VideoWriter ({filepath})")
                    return
                
                for f in all_frames:
                    # 強制縮放至初始化大小，避免 FFmpeg 因尺寸變換報錯
                    if f.shape[1] != w or f.shape[0] != h:
                        f = cv2.resize(f, (w, h))
                    out.write(f)
                    
                out.release()
                print(f"[Capture] 異常事件影片已儲存: {filepath}")
            except Exception as e:
                print(f"[Capture] 影片儲存失敗: {e}")

        threading.Thread(target=_record, daemon=True).start()

# 全域實例
pipeline = VideoCapturePipeline()
