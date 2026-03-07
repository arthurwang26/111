# [檔案用途：LINE Notify 通知推送邏輯] (⭐️負責通知推送的同學請專注修改此檔案⭐️)
import os
from dotenv import load_dotenv

load_dotenv()

from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN else None
except Exception as e:
    line_bot_api = None
    print(f"Warning: LINE SDK init failed: {e}")

from linebot.models import TextSendMessage, ImageSendMessage

def send_line_alert(description: str, image_path: str = None, level: int = 1) -> bool:
    """
    向設定的 LINE 使用者傳送推播通知。
    level 1: 一般訊息
    level 2: 警示訊息
    level 3: 緊急警報 (如果可以，會附帶照片)
    """
    if not line_bot_api or not LINE_USER_ID:
        prefix = ["INFO", "WARNING", "EMERGENCY"][level-1]
        print(f"[Mock LINE {prefix}] {description} (Image: {image_path})")
        return False

    try:
        messages = []
        
        if level == 3:
            text = f"🚨 [緊急異常警報] 🚨\n\n{description}"
        elif level == 2:
            text = f"⚠️ [系統警示] ⚠️\n\n{description}"
        else:
            text = f"ℹ️ [系統通知]\n\n{description}"
            
        messages.append(TextSendMessage(text=text))

        # 傳送照片: LINE Message API 需要使用對外公開的 HTTPS 網址
        # 如果您有串接 Imgur API 或是 Ngrok 公開網址，可以在這裡實作
        if image_path and level == 3:
            # TODO: 將 image_path 上傳到圖床或透過 Ngrok 轉換為 public_url
            # img_msg = ImageSendMessage(original_content_url=public_url, preview_image_url=public_url)
            # messages.append(img_msg)
            pass

        line_bot_api.push_message(LINE_USER_ID, messages)
        print(f"LINE 通知 (Level {level}) 傳送成功。")
        return True
    except LineBotApiError as e:
        print(f"LINE 通知傳送失敗: {e}")
        return False
