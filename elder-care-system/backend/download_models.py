"""
自動下載 MediaPipe Tasks 所需的官方預訓練模型。
執行方式：python download_models.py
"""
import os, urllib.request

# 模型下載目錄：
# 1. 優先讀取環境變數 MODEL_PATH
# 2. 如果是 Windows，預設使用 C:\elder_care_models
# 3. 其他環境（如 Docker/Linux）預設使用 ./models
MODELS_DIR = os.getenv("MODEL_PATH", r"C:\elder_care_models" if os.name == 'nt' else os.path.join(os.path.dirname(__file__), "models"))
os.makedirs(MODELS_DIR, exist_ok=True)

MODELS = {
    "pose_landmarker_heavy.task": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task"
    ),
    "face_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
    ),
}

def download():
    for name, url in MODELS.items():
        dest = os.path.join(MODELS_DIR, name)
        if os.path.exists(dest):
            print(f"[OK] {name} 已存在，跳過下載")
            continue
        print(f"[下載] {name} ...")
        urllib.request.urlretrieve(url, dest)
        size_mb = os.path.getsize(dest) / 1024 / 1024
        print(f"[完成] {name}  ({size_mb:.1f} MB)")

if __name__ == "__main__":
    download()
    print("\n所有模型已就緒！")
