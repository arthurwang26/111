# [檔案用途：追蹤與框線平滑化]
"""
時間平滑濾波器 (Temporal Smoothing)
降低 Bounding Box 閃爍與 Pose Landmarks 高頻抖動 (Jitter) 的工具
"""
import numpy as np

class EMASmoother:
    def __init__(self, alpha=0.5):
        """
        :param alpha: 平滑因子，界於 0~1。
                      數值越小，越遲鈍與平滑；
                      數值越大，越敏感且跟隨最新的偵測結果。
        """
        self.alpha = alpha
        self.state = None

    def update(self, measurement: np.ndarray) -> np.ndarray:
        if self.state is None:
            self.state = measurement.copy()
        else:
            self.state = self.alpha * measurement + (1 - self.alpha) * self.state
        return self.state

    def reset(self):
        self.state = None
