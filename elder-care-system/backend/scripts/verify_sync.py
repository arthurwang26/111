import requests
import time
import sys
import os

# 模擬前端切換鏡頭並檢查資料庫狀態同步
def verify_status_sync():
    api_base = "http://localhost:8000/api"
    video_base = "http://localhost:8000/video"
    
    print("1. 取得現有攝影機列表...")
    r = requests.get(f"{api_base}/cameras")
    cameras = r.json()
    if not cameras:
        print("沒有攝影機可測試")
        return
    
    target = cameras[0]
    cam_id = target['id']
    print(f"測試對象: ID {cam_id}, Name: {target['name']}, Current Status: {target['status']}")
    
    print(f"2. 觸發串流切換 (ID {cam_id})...")
    # 我們只需要發出請求觸發 update_source，不需要長時間讀取 StreamingResponse
    try:
        requests.get(f"{video_base}/stream?camera_id={cam_id}", timeout=2)
    except requests.exceptions.Timeout:
        pass # StreamingResponse 會超時是正常的
    
    print("3. 等待背景線程更新資料庫 (3秒)...")
    time.sleep(3)
    
    print("4. 再次檢查資料庫狀態...")
    r = requests.get(f"{api_base}/cameras")
    updated_cameras = r.json()
    target_updated = next((c for c in updated_cameras if c['id'] == cam_id), None)
    
    if target_updated:
        print(f"更新後狀態: {target_updated['status']}")
        if target_updated['status'] in ['active', 'connecting']:
            print("✅ 驗證成功: 資料庫狀態已同步！")
        else:
            print("❌ 驗證失敗: 狀態仍為 offline")
    else:
        print("找不到更新後的攝影機資料")

if __name__ == "__main__":
    verify_status_sync()
