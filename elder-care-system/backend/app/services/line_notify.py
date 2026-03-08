# [檔案用途：LINE Notify 通知推送邏輯] (⭐️負責通知推送的同學請專注修改此檔案⭐️)
import os
from dotenv import load_dotenv

load_dotenv()

from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
NGROK_URL = os.getenv("NGROK_URL", "").rstrip("/")

try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN else None
except Exception as e:
    line_bot_api = None
    print(f"Warning: LINE SDK init failed: {e}")


def _get_public_image_url(image_path: str) -> str | None:
    """
    將本地截圖路徑轉換為可公開存取的 HTTPS 網址。
    使用 NGROK_URL 環境變數作為前綴（需在 .env 設定）。
    """
    if not NGROK_URL or not image_path:
        return None
    try:
        filename = os.path.basename(image_path)
        return f"{NGROK_URL}/snapshots/{filename}"
    except Exception:
        return None


def send_line_alert(description: str, image_path: str = None, level: int = 1) -> bool:
    """
    向設定的 LINE 使用者傳送推播通知。
    level 1: 一般訊息
    level 2: 警示訊息（含截圖，若有 NGROK_URL）
    level 3: 緊急警報（含截圖，若有 NGROK_URL）
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

        # 傳送截圖：轉換本地路徑為 Ngrok 公開 URL
        if image_path and level >= 2:
            public_url = _get_public_image_url(image_path)
            if public_url:
                img_msg = ImageSendMessage(
                    original_content_url=public_url,
                    preview_image_url=public_url
                )
                messages.append(img_msg)
                print(f"[LINE] 附帶截圖: {public_url}")
            else:
                print("[LINE] NGROK_URL 未設定，跳過截圖附帶。請在 .env 設定 NGROK_URL。")

        line_bot_api.push_message(LINE_USER_ID, messages)
        print(f"LINE 通知 (Level {level}) 傳送成功。")
        return True
    except LineBotApiError as e:
        print(f"LINE 通知傳送失敗: {e}")
        return False
