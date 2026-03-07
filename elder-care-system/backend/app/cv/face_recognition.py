# [檔案用途：核心 人臉辨識模組] (⭐️負責辨識的同學請專注修改此檔案⭐️)
"""
臉部辨識模組 (V2)
您可以將這部分替換為更精準的模型 (例如 ArcFace, Dlib 等)
目前預設：使用 MediaPipe FaceLandmarker Pseudo-embeddings
"""
import numpy as np
from scipy.spatial.distance import cosine

class FaceRecognizer:
    def __init__(self):
        self.threshold = 0.85

    def extract_embedding(self, face_landmarks) -> np.ndarray:
        """
        從 FaceLandmarker 結果提取 embedding。
        如果要換成自己切下臉部丟入 ArcFace 模型，請改寫這裡。
        """
        pts = np.array([[lm.x, lm.y, lm.z] for lm in face_landmarks])
        flat = pts.flatten()
        if len(flat) >= 512:
            return flat[:512]
        return np.pad(flat, (0, 512 - len(flat)), "constant")

    def match_face(self, embedding: np.ndarray, registered_residents: list):
        """
        以 cosine similarity 比對已登記長者，回傳 (resident_id, name)。
        registered_residents 的格式為: [{"id": 1, "name": "王爺爺", "embedding": np.ndarray}, ...]
        """
        best_id, best_name, best_sim = None, "Unknown", -1
        for resident in registered_residents:
            sim = 1 - cosine(embedding, resident["embedding"])
            if sim > best_sim:
                best_sim, best_id, best_name = sim, resident["id"], resident["name"]
        
        if best_sim >= self.threshold:
            return best_id, best_name
        return None, "Unknown"

# 匯出實例供外部呼叫
face_recognizer = FaceRecognizer()
