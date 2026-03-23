# [檔案用途：核心 人臉辨識模組] 
"""
臉部辨識模組 (V2 - ArcFace Upgrade)
使用直接下載的 InsightFace pre-trained ONNX 模型 (w600k_r50.onnx)，
提供極高精度的 512-d embeddings 比對。
"""
import os
import cv2
import yaml
import numpy as np
import onnxruntime as ort
from scipy.spatial.distance import cosine

# 讀取 AI 設定檔
def load_ai_config():
    config_path = os.path.join(os.path.dirname(__file__), "../../../config/ai_config.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[Face] 讀取 ai_config.yaml 失敗，沿用預設設定: {e}")
        return {}

# 預設 112x112 臉部五官對齊標準點 (由 InsightFace 論文定義)
arcface_src = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041]
], dtype=np.float32)

class FaceRecognizer:
    def __init__(self):
        config = load_ai_config()
        ai_settings = config.get("ai", {})
        model_settings = config.get("models", {}).get("face_recognition", {})
        
        self.threshold = model_settings.get("similarity_threshold", 0.38)
        model_path = os.getenv("ARCFACE_MODEL_PATH", r"C:\elder_care_models\buffalo_l\w600k_r50.onnx")
        
        device = ai_settings.get("device", "cuda").lower()
        fallback_cpu = ai_settings.get("fallback_cpu", True)
        
        providers = []
        if device == "cuda":
            providers.append('CUDAExecutionProvider')
        if fallback_cpu or device == "cpu":
            providers.append('CPUExecutionProvider')
            
        try:
            self.session = ort.InferenceSession(model_path, providers=providers)
            active_providers = self.session.get_providers()
            self.input_name = self.session.get_inputs()[0].name
            self._ready = True
            print(f"[Face] ArcFace ONNX Model 載入成功！運行於: {active_providers[0]}")
        except Exception as e:
            print(f"[Face] ArcFace 模型載入失敗: {e}")
            self._ready = False

    def align_face(self, img_bgr: np.ndarray, mediapipe_landmarks) -> np.ndarray:
        """
        透過 MediaPipe 提供的特徵點，計算放射變換矩陣，將人臉裁切並擺正至 112x112。
        """
        h, w = img_bgr.shape[:2]
        # 對應的五官：右眼(33), 左眼(263), 鼻尖(1), 右嘴角(61), 左嘴角(291)
        pts = np.array([
            [mediapipe_landmarks[33].x * w, mediapipe_landmarks[33].y * h],
            [mediapipe_landmarks[263].x * w, mediapipe_landmarks[263].y * h],
            [mediapipe_landmarks[1].x * w, mediapipe_landmarks[1].y * h],
            [mediapipe_landmarks[61].x * w, mediapipe_landmarks[61].y * h],
            [mediapipe_landmarks[291].x * w, mediapipe_landmarks[291].y * h]
        ], dtype=np.float32)

        # 計算放射變換矩陣
        tform, _ = cv2.estimateAffinePartial2D(pts, arcface_src)
        if tform is None:
            return None
        
        # 將臉部圖像裁切對齊至 (112, 112)
        aligned_img = cv2.warpAffine(img_bgr, tform, (112, 112))
        return aligned_img

    def extract_embedding(self, img_bgr: np.ndarray, mediapipe_landmarks) -> np.ndarray:
        """
        獲得對正的臉部後，輸入 ArcFace 提取 512 維身份特徵向量。
        """
        if not self._ready or img_bgr is None:
            return np.zeros(512, dtype=np.float32).tolist()
            
        aligned = self.align_face(img_bgr, mediapipe_landmarks)
        if aligned is None:
            return np.zeros(512, dtype=np.float32).tolist()

        # ArcFace 預處理: BGR轉RGB -> 歸一化 [-1, 1] -> 通道轉置 (C, H, W)
        aligned = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB)
        aligned = (aligned.astype(np.float32) - 127.5) / 127.5
        aligned = np.transpose(aligned, (2, 0, 1))
        input_tensor = np.expand_dims(aligned, axis=0)

        # ONNX 推論提取 512-d 特徵
        embedding = self.session.run(None, {self.input_name: input_tensor})[0][0]
        
        # 進行 L2 正規化 (Cosine similarity 必須在正規化向量上才準確)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding.tolist()

    def match_face(self, embedding_list: list, registered_residents: list):
        """
        以 ArcFace 512 維基準，進行餘弦相似度對比。
        """
        if not registered_residents or not self._ready:
            return None, "Unknown"
            
        embedding = np.array(embedding_list, dtype=np.float32)
        
        # 若是全零陣列(辨識失敗或防護)，跳過比對
        if np.all(embedding == 0):
            return None, "Unknown"

        best_id, best_name, best_sim = None, "Unknown", -1
        for resident in registered_residents:
            res_emb = np.array(resident["embedding"], dtype=np.float32)
            sim = 1 - cosine(embedding, res_emb)
            if sim > best_sim:
                best_sim, best_id, best_name = sim, resident["id"], resident["name"]
        
        if best_sim >= self.threshold:
            print(f"[Face-ArcFace] 身份匹配成功: {best_name} (信心度: {best_sim:.4f})")
            return best_id, best_name
            
        return None, "Unknown"

# 匯出實例供外部呼叫
face_recognizer = FaceRecognizer()
