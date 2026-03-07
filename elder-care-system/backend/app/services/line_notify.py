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

def send_line_alert(message: str, image_path: str = None) -> bool:
    """向設定的 LINE 使用者傳送推播通知。"""
    if not line_bot_api or not LINE_USER_ID:
        print(f"[Mock LINE Alert] {message}")
        return False

    try:
        text = f"🚨 長照系統警報 🚨\n\n{message}"
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        print("LINE 通知傳送成功。")
        return True
    except LineBotApiError as e:
        print(f"LINE 通知傳送失敗: {e}")
        return False
