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
        # 提高閾值，因為歸一化後特徵會更接近
        self.threshold = 0.75

    def _normalize_landmarks(self, face_landmarks) -> np.ndarray:
        """
        將臉部特徵點進行歸一化：
        1. 以鼻尖(landmark 1)為中心
        2. 以兩眼距離為縮放基準
        """
        pts = np.array([[lm.x, lm.y, lm.z] for lm in face_landmarks])
        
        # 1. 平移：以鼻尖為座標原點 (Landmark 1 通常是鼻尖)
        nose = pts[1]
        pts = pts - nose
        
        # 2. 縮放：計算兩眼距離 (Landmark 33 號左右與 263 號左右分別是兩眼)
        eye1 = pts[33]
        eye2 = pts[263]
        dist = np.linalg.norm(eye1 - eye2)
        
        if dist > 0:
            pts = pts / dist
            
        return pts.flatten()

    def extract_embedding(self, face_landmarks) -> np.ndarray:
        """
        從 FaceLandmarker 結果提取歸一化後的 embedding。
        """
        flat = self._normalize_landmarks(face_landmarks)
        # 取前 512 維 (Landmarks 有 478 點 -> 1434 維)
        if len(flat) >= 512:
            return flat[:512]
        return np.pad(flat, (0, 512 - len(flat)), "constant")

    def match_face(self, embedding: np.ndarray, registered_residents: list):
        """
        以餘弦相似度比對，回傳 (resident_id, name)。
        """
        if not registered_residents:
            return None, "Unknown"
            
        best_id, best_name, best_sim = None, "Unknown", -1
        for resident in registered_residents:
            res_emb = np.array(resident["embedding"])
            sim = 1 - cosine(embedding, res_emb)
            # [LOG] 記錄每一位匹配過的相似度，方便調優
            print(f"[Debug-Face] 比對 {resident['name']} 目標相似度: {sim:.4f}")
            if sim > best_sim:
                best_sim, best_id, best_name = sim, resident["id"], resident["name"]
        
        if best_sim >= self.threshold:
            print(f"[Face] !!! 匹配成功: {best_name} (相似度: {best_sim:.4f}) !!!")
            return best_id, best_name
            
        return None, "Unknown"

# 匯出實例供外部呼叫
face_recognizer = FaceRecognizer()
