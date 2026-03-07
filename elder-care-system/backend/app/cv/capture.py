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
        # 嘗試從環境變數讀取 CAMERA_SOURCE，若無則使用傳入的預設值
        env_source = os.getenv("CAMERA_SOURCE", source)
        try:
            self.source = int(env_source)
        except (ValueError, TypeError):
            self.source = env_source
            
        self.cap = cv2.VideoCapture(self.source)
        self.running = False
        self.current_frame = None
        self.lock = threading.Lock()
        
        # Ring buffer for pre-event frames
        self.buffer_size = buffer_seconds * fps
        self.frame_buffer = collections.deque(maxlen=self.buffer_size)
        self.fps = fps
        
        print(f"[Capture] 影像來源已設定為: {self.source}, 緩衝區: {self.buffer_size} 幀")
        
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
            
    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print(f"[Capture] 無法擷取影像 {self.source}，嘗試重新連線...")
                self.cap.release()
                time.sleep(2)
                self.cap = cv2.VideoCapture(self.source)
                continue
                
            with self.lock:
                self.current_frame = frame
                self.frame_buffer.append(frame.copy())
                
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
            h, w = all_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'avc1') # Use H264 codec for web compatibility
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            out = cv2.VideoWriter(filepath, fourcc, self.fps, (w, h))
            
            for f in all_frames:
                out.write(f)
                
            out.release()
            print(f"[Capture] 異常事件影片已儲存: {filepath}")

        threading.Thread(target=_record, daemon=True).start()

# 全域實例
pipeline = VideoCapturePipeline()
