# [檔案用途：多目標追蹤邏輯]
"""
輕量化多目標追蹤器 (SORT-like IOU Tracker)
利用 IoU 與匈牙利演算法 (Hungarian Algorithm) 對偵測框進行身份關聯 (Identity Association)，
能保證短暫遮蔽或偵測失敗時 (max_age 以內) 保持相同的 Track ID。
如此一來，同一個人物只需在剛進入畫面時做一次 ArcFace 臉部辨識，後續皆依賴 Tracking 以極大化降低 CPU 消耗。
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from .smoothing import EMASmoother

def calc_iou(boxA, boxB):
    # box: [x1, y1, x2, y2]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
    return iou

class Track:
    def __init__(self, bbox, track_id):
        self.track_id = track_id
        self.bbox = bbox # 原始最新測量框 [x1, y1, x2, y2]
        self.time_since_update = 0
        self.hits = 1
        
        # 身份與姿態綁定
        self.resident_id = None
        self.resident_name = "Unknown"
        self.posture = "Unknown"
        
        # 平滑器 (EMA)
        self.bbox_smoother = EMASmoother(alpha=0.6)
        self.smoothed_bbox = self.bbox_smoother.update(np.array(bbox))

    def predict(self):
        # 預測階段：若是無法預測的靜態追蹤，直接時間增加並回傳平滑框
        self.time_since_update += 1
        return self.smoothed_bbox

    def update(self, bbox, posture="Unknown"):
        self.time_since_update = 0
        self.hits += 1
        self.bbox = bbox
        self.posture = posture if posture != "Unknown" else self.posture
        self.smoothed_bbox = self.bbox_smoother.update(np.array(bbox))

class IouTracker:
    def __init__(self, max_age=15, min_hits=1, iou_threshold=0.3):
        """
        max_age: 容許目標消失的幀數，若超出則移除
        min_hits: 必須被偵測到幾次才被視為有效 Track
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks = []
        self.track_id_counter = 1

    def update(self, detections: list, postures: list = None):
        """
        detections: list of bounding boxes [x1, y1, x2, y2]
        postures: list of strings (例如 "Standing", "Lying")
        Return list of active Tracks (Confirmed tracks only)
        """
        if postures is None:
            postures = ["Unknown"] * len(detections)

        # 1. 若追蹤庫為空，全部視為新目標
        if len(self.tracks) == 0:
            for i, det in enumerate(detections):
                trk = Track(det, self.track_id_counter)
                trk.posture = postures[i]
                self.tracks.append(trk)
                self.track_id_counter += 1
            return self.tracks

        # 2. 如果當前完全沒偵測到人，所有 Track 老化
        if len(detections) == 0:
            for trk in self.tracks:
                trk.predict()
            self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]
            return [t for t in self.tracks if t.time_since_update == 0]

        # 3. 準備預測矩陣與 IoU 距離矩陣
        predictions = np.array([t.predict() for t in self.tracks])
        iou_matrix = np.zeros((len(predictions), len(detections)), dtype=np.float32)

        for i, trk_bbox in enumerate(predictions):
            for j, det_bbox in enumerate(detections):
                iou_matrix[i, j] = calc_iou(trk_bbox, det_bbox)

        # 匈牙利演算法 (Hungarian Assignment) 取最大 IoU
        row_ind, col_ind = linear_sum_assignment(-iou_matrix)

        unmatched_tracks = set(range(len(self.tracks)))
        unmatched_detections = set(range(len(detections)))
        matched_indices = []

        for r, c in zip(row_ind, col_ind):
            if iou_matrix[r, c] >= self.iou_threshold:
                matched_indices.append((r, c))
                unmatched_tracks.remove(r)
                unmatched_detections.remove(c)

        # 4. 更新成功匹配的 Tracks
        for r, c in matched_indices:
            self.tracks[r].update(detections[c], postures[c])

        # 5. 處理尚未匹配上的偵測框，建立新 Track
        for c in unmatched_detections:
            trk = Track(detections[c], self.track_id_counter)
            trk.posture = postures[c]
            self.tracks.append(trk)
            self.track_id_counter += 1

        # 6. 清理掉過期的 Tracks
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

        # 回傳活躍的 Tracks (近期有更新的)
        return [t for t in self.tracks if t.hits >= self.min_hits and t.time_since_update == 0]

tracker = IouTracker()
