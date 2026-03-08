# [檔案用途：核心 AI 處理與姿勢辨識] (⭐️負責辨識的兩位同學請專注修改此檔案⭐️ 可以自由調整跌倒判斷邏輯和閾值)
"""
CV 處理器 - 使用 mediapipe.tasks Vision API（新版，0.10.x 相容）
支援：
  - 姿態辨識 (PoseLandmarker) → 跌倒偵測
  - 臉部辨識 (FaceLandmarker) → 長者識別（embedding 比對）
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from sqlalchemy.orm import Session
from ..db import Resident

# Import new modular architecture
from .face_recognition import face_recognizer
from .anomaly_rules import anomaly_engine

_BASE = os.getenv("MODEL_PATH", r"C:\elder_care_models" if os.name == 'nt' else "/app/models")
POSE_MODEL = os.path.join(_BASE, "pose_landmarker_heavy.task")
FACE_MODEL = os.path.join(_BASE, "face_landmarker.task")

class CVProcessor:
    def __init__(self):
        self.registered_residents: list = []
        self._frame_count = 0
        self._init_models()

    def _init_models(self):
        """初始化 PoseLandmarker 與 FaceLandmarker（Tasks API）。"""
        try:
            # Pose
            pose_opts = mp_python.BaseOptions(model_asset_path=POSE_MODEL)
            pose_options = mp_vision.PoseLandmarkerOptions(
                base_options=pose_opts,
                running_mode=VisionTaskRunningMode.IMAGE,
                num_poses=5,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                output_segmentation_masks=False,
            )
            self.pose_detector = mp_vision.PoseLandmarker.create_from_options(pose_options)

            # Face
            face_opts = mp_python.BaseOptions(model_asset_path=FACE_MODEL)
            face_options = mp_vision.FaceLandmarkerOptions(
                base_options=face_opts,
                running_mode=VisionTaskRunningMode.IMAGE,
                num_faces=5,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
            )
            self.face_detector = mp_vision.FaceLandmarker.create_from_options(face_options)
            self._ready = True
            print("[CV] MediaPipe Tasks API 初始化成功")
        except Exception as e:
            print(f"[CV] 模型初始化失敗（Mock 模式）: {e}")
            self.pose_detector = None
            self.face_detector = None
            self._ready = False

    def refresh_residents(self, db: Session):
        """從資料庫重新載入長者 embedding 快取。"""
        residents = db.query(Resident).filter(Resident.face_embedding != None).all()
        self.registered_residents = [
            {"id": r.id, "name": r.name, "embedding": np.array(r.face_embedding)}
            for r in residents
        ]

    def determine_posture(self, pose_landmarks) -> str:
        """以肩膀/髖部 Y 軸差值判斷姿態（Standing / Sitting / Lying）。"""
        if not pose_landmarks:
            return "Unknown"
        try:
            ls, rs = pose_landmarks[11], pose_landmarks[12]
            lh, rh = pose_landmarks[23], pose_landmarks[24]
            avg_shoulder_y = (ls.y + rs.y) / 2
            avg_hip_y = (lh.y + rh.y) / 2
            diff = abs(avg_shoulder_y - avg_hip_y)
            if diff < 0.15:
                return "Lying"
            elif avg_shoulder_y < avg_hip_y - 0.3:
                return "Standing"
            else:
                return "Sitting"
        except (IndexError, AttributeError):
            return "Unknown"
            
    def detect_objects(self, frame) -> str:
        """
        [TODO] 在此處擴充 YOLO 或 Object Detection 模型，
        回傳偵測到的互動特徵字串 (例如 "wheelchair", "knife" 等)
        """
        return ""

    def process_frame(self, frame: np.ndarray, db: Session):
        """
        主處理入口 - 整合 Frame Sampling 與 Multi-Object Tracking
        """
        import time
        start_time = time.time()
        self._frame_count += 1
        
        if not self.registered_residents and self._frame_count % 100 == 1:
            self.refresh_residents(db)

        if not self._ready:
            cv2.putText(frame, "Mock CV Mode (模型未就緒)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return frame, [], "Unknown"


        from .tracking import tracker

        # 每 3 幀做一次 Full Detection (Detection Interval 節省 CPU)
        run_detection = (self._frame_count % 3 == 1)
        
        active_tracks = []
        object_interaction = self.detect_objects(frame)
        h, w = frame.shape[:2]

        if run_detection:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # 1. Pose Detection (用以獲取人體姿態與整體 Bounding Box)
            pose_result = self.pose_detector.detect(mp_image)
            detections_bboxes = []
            postures = []
            
            if pose_result.pose_landmarks:
                for person_landmarks in pose_result.pose_landmarks:
                    posture = self.determine_posture(person_landmarks)
                    xs = [lm.x * w for lm in person_landmarks]
                    ys = [lm.y * h for lm in person_landmarks]
                    x1, y1 = max(0, min(xs)), max(0, min(ys))
                    x2, y2 = min(w, max(xs)), min(h, max(ys))
                    
                    padding = 20
                    detections_bboxes.append([max(0, x1-padding), max(0, y1-padding), min(w, x2+padding), min(h, y2+padding)])
                    postures.append(posture)

            # 2. Tracking 更新 (產生或關聯 Identity)
            active_tracks = tracker.update(detections_bboxes, postures)

            # 3. 臉部辨識 (ArcFace) 只對「尚未辨識出身份的 Track」執行
            unidentified_tracks = [t for t in active_tracks if t.resident_id is None]
            if unidentified_tracks:
                face_result = self.face_detector.detect(mp_image)
                if face_result.face_landmarks:
                    for face_lms in face_result.face_landmarks:
                        fxs = [lm.x * w for lm in face_lms]
                        fys = [lm.y * h for lm in face_lms]
                        fx1, fy1, fx2, fy2 = min(fxs), min(fys), max(fxs), max(fys)
                        face_cx, face_cy = (fx1 + fx2) / 2, (fy1 + fy2) / 2
                        
                        # 把臉部分派給對應的 Track
                        matched_track = None
                        for trk in unidentified_tracks:
                            tx1, ty1, tx2, ty2 = trk.smoothed_bbox
                            # 若臉部中心點在人體框內
                            if tx1 - 10 <= face_cx <= tx2 + 10 and ty1 - 10 <= face_cy <= ty2 + 10:
                                matched_track = trk
                                break
                        
                        if matched_track:
                            emb_list = face_recognizer.extract_embedding(frame, face_lms)
                            res_id, res_name = face_recognizer.match_face(emb_list, self.registered_residents)
                            if res_id:
                                matched_track.resident_id = res_id
                                matched_track.resident_name = res_name
        else:
            # 非偵測幀，純預測追蹤框位置，平滑過渡
            active_tracks = tracker.update([], [])

        recognized_names = []
        global_posture = "Unknown"
        active_track_count = len(active_tracks)

        # 4. 繪製平滑框與判定異常事件
        for trk in active_tracks:
            # 取得經 EMA 平滑化的 Track 框線
            tx1, ty1, tx2, ty2 = map(int, trk.smoothed_bbox)
            name = trk.resident_name
            posture = trk.posture
            
            global_posture = posture if posture != "Unknown" else global_posture
            if name != "Unknown":
                recognized_names.append(name)
            
            # 繪製平滑框 (大幅減少 UI Jitter)
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), color, 2)
            label = f"ID:{trk.track_id} {name} [{posture}]"
            cv2.putText(frame, label, (tx1, max(20, ty1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            
            # 將完整的 Tracking Entity 餵給異常判斷引擎，以實作更嚴格的防誤報邏輯
            if trk.resident_id:
                anomaly_engine.evaluate(trk.resident_id, name, posture, object_interaction, frame, db, trk)

                # 定期紀錄日常行為
                if self._frame_count % 300 == 0:
                    from ..db import Event
                    try:
                        new_event = Event(
                            resident_id=trk.resident_id,
                            activity_type=posture.lower(),
                            object_interaction=object_interaction if object_interaction else None,
                            description=f"偵測到 {name} 正在 {posture}"
                        )
                        db.add(new_event)
                        db.commit()
                    except Exception as e:
                        db.rollback()

        # 5. AI Inference Latency & Metrics Logging (每 300 幀記錄一次)
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        if self._frame_count % 300 == 0:
            from ..db import SystemMetric
            try:
                # 簡單計算過去 300 幀的估計 FPS (不含 sleep)
                approx_fps = 1000.0 / (latency_ms + 1e-5)
                new_metric = SystemMetric(
                    ai_latency_ms=latency_ms,
                    camera_fps=approx_fps,
                    active_tracks=active_track_count
                )
                db.add(new_metric)
                db.commit()
            except Exception as e:
                db.rollback()

        return frame, recognized_names, global_posture

processor = CVProcessor()
