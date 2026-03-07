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
        主處理入口：
        1. 執行姿態辨識
        2. 執行臉部辨識
        3. 執行異常判定 (anomaly_rules.py)
        4. 繪製標注
        """
        if not self._ready:
            cv2.putText(frame, "Mock CV Mode (模型未就緒)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return frame, [], "Unknown"

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        h, w = frame.shape[:2]

        posture = "Unknown"
        pose_result = self.pose_detector.detect(mp_image)
        if pose_result.pose_landmarks:
            for person_landmarks in pose_result.pose_landmarks:
                posture = self.determine_posture(person_landmarks)
                for lm in person_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

        recognized_names = []
        face_result = self.face_detector.detect(mp_image)
        object_interaction = self.detect_objects(frame)
        
        if face_result.face_landmarks:
            for face_lms in face_result.face_landmarks:
                emb = face_recognizer.extract_embedding(face_lms)
                resident_id, name = face_recognizer.match_face(emb, self.registered_residents)
                recognized_names.append(name)
                
                # ------ 呼叫異常判斷引擎 ------
                if resident_id:
                    anomaly_engine.evaluate(resident_id, name, posture, object_interaction, frame, db)

                # 繪製邊框
                xs = [int(lm.x * w) for lm in face_lms]
                ys = [int(lm.y * h) for lm in face_lms]
                x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{name} [{posture}]"
                cv2.putText(frame, label, (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        return frame, recognized_names, posture

processor = CVProcessor()
