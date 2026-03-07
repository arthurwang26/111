# [檔案用途：生成事件摘要與分析] (⭐️負責產出描述的同學請專注修改此檔案⭐️)
"""
大型語言模型 (LLM) 分析產生器
用於透過 OpenAI / Gemini API 分析 `DailyActivity` 和 `AbnormalEvent`，
自動產出給家屬看的「每日活動摘要」或「異常事件文字描述」。
"""
import os

class LLMSummarizer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate_event_description(self, resident_name: str, event_type: str, posture: str, object_detected: str) -> str:
        """
        [TODO: 串接真實 GPT API]
        當異常事件發生時，動態生成一段更通順的文字敘述，替代寫死的字串。
        """
        prompt = f"請用繁體中文以溫暖的口吻描述以下長照中心事件: 長者 {resident_name} 目前姿勢為 {posture}，發生了 {event_type} 事件，周遭有 {object_detected}。"
        # res = openai.ChatCompletion.create(messages=[{"role": "user", "content": prompt}], ...)
        
        # 目前暫時回傳 Dummy 寫死的字串，待同學們實作
        return f"{resident_name} 長者疑似發生了 {event_type} (姿勢: {posture})，請工作人員盡速確認。"

    def generate_daily_summary(self, resident_name: str, walking_mins: float, sitting_mins: float, sleeping_mins: float) -> str:
        """
        [TODO: 串接真實 GPT API]
        每天晚上統整這位長者白天的活動量，產生日報表。
        """
        if not self.api_key:
            return f"{resident_name} 今日活動紀錄摘要: 白天主要在休息，走動時間約 {int(walking_mins)} 分鐘。"

        # 如果有 API Key，可將數據轉換成 prompt 呼叫大模型
        return f"AI 摘要: {resident_name} 今日整體活動量正常，請繼續保持。"

summarizer = LLMSummarizer()
