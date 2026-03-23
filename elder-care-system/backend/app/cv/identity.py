# [檔案用途：身份管理器 Identity Manager]
import numpy as np
import time
from typing import Dict, Optional, Tuple
from collections import deque

class IdentityManager:
    """
    Identity Manager 負責維持系統中人物身份 (Person ID) 的穩定性。
    當由 ByteTrack 給出的 Track ID 消失並重新出現時 (可能因遮擋或離開畫面)，
    此模組會結合「臉部 Embedding」與「時序連續性」重新關聯原來的 Person ID。
    """
    def __init__(self, cache_timeout: int = 5):
        # 紀錄已註冊長者的 {id: name, embedding} (來自資料庫)
        self.registered_residents: Dict[int, dict] = {}
        
        # Track ID 到 Person ID 的快取映射
        # { track_id: {"person_id": id, "name": name, "last_seen": timestamp, "face_emb": embedding} }
        self.track_to_person: Dict[int, dict] = {}
        
        # 遺失的軌跡暫存區，用於當 Track ID 更換時，若特徵相似度高，可秒接上
        # { person_id: {"last_seen": timestamp, "face_emb": embedding} }
        self.lost_person_cache: Dict[int, dict] = {}
        
        self.cache_timeout = cache_timeout  # 秒

    def update_registered_residents(self, residents_list: list):
        """由上層傳入資料庫中已建檔的長者特徵陣列"""
        self.registered_residents = {r["id"]: r for r in residents_list}

    def clean_stale_tracks(self):
        """定期清理過期未出現的 Track ID 與 Person 快取"""
        now = time.time()
        
        # 1. 搬移過期的 Track 到 Lost Person Cache
        expired_tracks = []
        for tid, data in self.track_to_person.items():
            if now - data["last_seen"] > self.cache_timeout:
                expired_tracks.append(tid)
                if data["person_id"] is not None:
                    # 保存進 lost cache 供日後 ReID 比對
                    self.lost_person_cache[data["person_id"]] = {
                        "last_seen": data["last_seen"],
                        "face_emb": data["face_emb"]
                    }
                    
        for tid in expired_tracks:
            self.track_to_person.pop(tid, None)
            
        # 2. 清理過期太久的 Lost Person Cache (例如 600 秒未見)
        expired_lost = [pid for pid, d in self.lost_person_cache.items() if now - d["last_seen"] > 600]
        for pid in expired_lost:
            self.lost_person_cache.pop(pid, None)

    def resolve_identity(self, track_id: int, detected_face_emb: list, face_matcher) -> Tuple[Optional[int], str]:
        """
        核心邏輯：判斷傳入的 Track ID 屬於哪位 Person。
        流程：Detection -> ByteTrack -> Face Recognition -> [Identity Manager]
        """
        now = time.time()
        
        # 若這個 Track ID 已經綁定過有名字的 Person，且沒有給出新的強烈臉部特徵覆寫，直接沿用
        if track_id in self.track_to_person:
            cached = self.track_to_person[track_id]
            cached["last_seen"] = now
            # 若這次有抽出新的臉部向量，可以考慮平滑更新 (移動平均)，先簡單覆蓋或直接用舊的
            if detected_face_emb and not np.all(np.array(detected_face_emb) == 0):
                cached["face_emb"] = detected_face_emb
            return cached["person_id"], cached["name"]

        # 這是一個全新的 Track ID (或者剛被清理掉的)
        # 嘗試進行臉部辨識 (ArcFace Matcher)
        matched_id, matched_name = face_matcher.match_face(detected_face_emb, list(self.registered_residents.values()))
        
        if matched_id is not None:
            # 辨識成功，將此 Track ID 正式綁定到這個 Person ID
            self.track_to_person[track_id] = {
                "person_id": matched_id,
                "name": matched_name,
                "last_seen": now,
                "face_emb": detected_face_emb
            }
            # 如果這個人之前在 lost cache 裡面，把他拿出來
            if matched_id in self.lost_person_cache:
                self.lost_person_cache.pop(matched_id, None)
        else:
            # 辨識失敗或無特徵，先標記為 Unknown，等待後續更新
            self.track_to_person[track_id] = {
                "person_id": None,
                "name": "Unknown",
                "last_seen": now,
                "face_emb": detected_face_emb
            }
            
        return int(matched_id) if matched_id is not None else None, str(matched_name)

# 全域單例
identity_manager = IdentityManager()
