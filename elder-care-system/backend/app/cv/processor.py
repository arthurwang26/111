# [檔案用途：核心 AI 處理與姿勢辨識]
import os
import cv2
import numpy as np
from ultralytics import YOLO

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from sqlalchemy.orm import Session
from ..db import Resident
import yaml

# Import new modular architecture
from .face_recognition import face_recognizer
from .anomaly_rules import anomaly_engine
from .identity import identity_manager

_BASE = os.getenv("MODEL_PATH", r"C:\elder_care_models" if os.name == 'nt' else "/app/models")
FACE_MODEL = os.path.join(_BASE, "face_landmarker.task")
YOLO_MODEL = os.path.join(_BASE, "yolov8n-pose.pt")

class TrackedPerson:
    def __init__(self, track_id, bbox, posture):
        self.track_id = track_id
        self.smoothed_bbox = bbox
        self.posture = posture
        self.resident_id = None
        self.resident_name = "Unknown"

class CVProcessor:
    def __init__(self):
        self.registered_residents: list = []
        self._frame_count = 0
        self.active_tracks = {}
        self._init_models()

    def _init_models(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../../config/ai_config.yaml")
            device = "cuda"
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    device = config.get("ai", {}).get("device", "cuda").lower()
            except:
                pass

            self.model = YOLO(YOLO_MODEL)
            if device == "cuda":
                self.model.to("cuda")
                print("[CV] YOLOv8-Pose 強制派發至 CUDA")
                
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
            print("[CV] YOLOv8-Pose + MP Face 初始化成功")
        except Exception as e:
            print(f"[CV] 模型初始化失敗: {e}")
            self._ready = False

    def refresh_residents(self, db: Session):
        residents = db.query(Resident).filter(Resident.face_embedding != None).all()
        self.registered_residents = [
            {"id": r.id, "name": r.name, "embedding": np.array(r.face_embedding)}
            for r in residents
        ]
        identity_manager.update_registered_residents(self.registered_residents)
        
    def detect_objects(self, frame) -> str:
        return ""

    def process_frame(self, frame: np.ndarray, db: Session):
        import time
        start_time = time.time()
        self._frame_count += 1
        
        if not self.registered_residents and self._frame_count % 100 == 1:
            self.refresh_residents(db)

        if not self._ready:
            cv2.putText(frame, "Mock CV Mode (模型未就緒)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return frame, [], "Unknown"

        # 每隔 2 幀才追蹤，讓 FPS 上升 (YOLOv8 ByteTrack 有時需要連貫，但可降頻)
        # 不降頻 YOLOv8n 在 CPU 可能慢，先全速跑，如果不順再補降頻邏輯
        results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)
        result = results[0]
        
        # 原生骨架與追蹤框繪圖 (極度美觀)
        annotated_frame = result.plot(boxes=False, labels=False, kpt_radius=3, kpt_line=True)
        
        h, w = frame.shape[:2]
        recognized_names = []
        global_posture = "Unknown"
        active_track_count = 0
        
        object_interaction = self.detect_objects(frame)
        current_tracks = []
        
        if result.boxes is not None and result.boxes.id is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            track_ids = result.boxes.id.int().cpu().numpy()
            
            if hasattr(result, 'keypoints') and result.keypoints is not None:
                keypoints_data = result.keypoints.data.cpu().numpy() # [N, 17, 3] usually
            else:
                keypoints_data = [None] * len(boxes)
                
            active_track_count = len(boxes)
            
            for box, track_id, keypoints in zip(boxes, track_ids, keypoints_data):
                x1, y1, x2, y2 = box
                
                if track_id not in self.active_tracks:
                    self.active_tracks[track_id] = TrackedPerson(track_id, box, "Unknown")
                    
                trk = self.active_tracks[track_id]
                
                # EMA 降低框線抖動
                alpha = 0.5
                trk.smoothed_bbox = [
                    trk.smoothed_bbox[0] * (1-alpha) + x1 * alpha,
                    trk.smoothed_bbox[1] * (1-alpha) + y1 * alpha,
                    trk.smoothed_bbox[2] * (1-alpha) + x2 * alpha,
                    trk.smoothed_bbox[3] * (1-alpha) + y2 * alpha
                ]
                
                posture = anomaly_engine.determine_posture_yolo(keypoints, box)
                trk.posture = posture
                current_tracks.append(trk)

            # Face Recognition
            unidentified_tracks = [t for t in current_tracks if t.resident_id is None]
            
            # Rate limit variables
            import time
            current_time = time.time()
            if not hasattr(self, '_face_check_cooldowns'):
                self._face_check_cooldowns = {}
                
            # Filter tracks that are on cooldown (try once every 1.5 seconds)
            ready_to_check_tracks = []
            for t in unidentified_tracks:
                if current_time - self._face_check_cooldowns.get(t.track_id, 0) > 1.5:
                    ready_to_check_tracks.append(t)
                    
            if ready_to_check_tracks and self.face_detector:
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    face_result = self.face_detector.detect(mp_image)
                    
                    if face_result and face_result.face_landmarks:
                        for face_lms in face_result.face_landmarks:
                            fxs = [lm.x * w for lm in face_lms]
                            fys = [lm.y * h for lm in face_lms]
                            fx1, fy1, fx2, fy2 = min(fxs), min(fys), max(fxs), max(fys)
                            face_cx, face_cy = (fx1 + fx2) / 2, (fy1 + fy2) / 2
                            
                            cv2.rectangle(annotated_frame, (int(fx1), int(fy1)), (int(fx2), int(fy2)), (255, 200, 0), 2)
                            cv2.putText(annotated_frame, "Face Detected", (int(fx1), max(10, int(fy1)-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)
                            
                            matched_track = None
                            for trk in ready_to_check_tracks:
                                tx1, ty1, tx2, ty2 = trk.smoothed_bbox
                                if tx1 - 10 <= face_cx <= tx2 + 10 and ty1 - 10 <= face_cy <= ty2 + 10:
                                    matched_track = trk
                                    break
                            
                            if matched_track:
                                # Apply cooldown immediately
                                self._face_check_cooldowns[matched_track.track_id] = current_time
                                
                                emb_list = face_recognizer.extract_embedding(frame, face_lms)
                                matched_track._temp_face_emb = emb_list
                                
                except Exception as e:
                    print(f"[Face] 臉部辨識發生錯誤，略過此幀: {e}")

        # 使用 IdentityManager 解析持續的身分
        for trk in current_tracks:
            extracted_face_emb = getattr(trk, "_temp_face_emb", None)
            
            # 委託 IdentityManager 解析此軌跡的身分
            resolved_id, resolved_name = identity_manager.resolve_identity(
                trk.track_id, 
                extracted_face_emb, 
                face_recognizer
            )
            
            trk.resident_id = resolved_id
            trk.resident_name = resolved_name
            
            # 清理暫存
            if hasattr(trk, "_temp_face_emb"):
                delattr(trk, "_temp_face_emb")
                
        # 定期清理舊軌跡 Cache
        if self._frame_count % 300 == 0:
            identity_manager.clean_stale_tracks()

        current_track_ids = {t.track_id for t in current_tracks}
        self.active_tracks = {k: v for k, v in self.active_tracks.items() if k in current_track_ids}

        for trk in current_tracks:
            tx1, ty1, tx2, ty2 = map(int, trk.smoothed_bbox)
            name = trk.resident_name
            posture = trk.posture
            
            global_posture = posture if posture != "Unknown" else global_posture
            if name != "Unknown":
                recognized_names.append(name)
            
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            # 自行畫出平滑框，取代原本 plot 會閃爍的框
            cv2.rectangle(annotated_frame, (tx1, ty1), (tx2, ty2), color, 2)
            label = f"ID:{trk.track_id} {name} [{posture}]"
            cv2.putText(annotated_frame, label, (tx1, max(20, ty1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            if trk.resident_id:
                anomaly_engine.evaluate(trk.resident_id, name, posture, object_interaction, annotated_frame, db, trk)

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

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        if self._frame_count % 300 == 0:
            from ..db import SystemMetric
            try:
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

        return annotated_frame, recognized_names, global_posture

processor = CVProcessor()
