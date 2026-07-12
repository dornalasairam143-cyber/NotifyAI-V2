import requests
import logging
from typing import Dict, Any
from config import config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Handles formatting and sending messages to Telegram via API."""
    
    def __init__(self) -> None:
        self.token = config.TELEGRAM_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_alert(self, article_name: str, website: str, notification: Dict[str, str], ai_data: Dict[str, Any]) -> None:
        """Formats and sends a beautiful alert message."""
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials missing. Skipping notification.")
            return

        message = (
            f"🚨 *WEBSITE UPDATE DETECTED*\n\n"
            f"📌 *Article:* {article_name}\n"
            f"🏢 *Website:* {website}\n"
            f"📄 *Notification:* {notification['title']}\n\n"
            f"📊 *Category:* {ai_data.get('Category')}\n"
            f"⚡ *Status:* {ai_data.get('Status')}\n"
            f"🎯 *Confidence:* {ai_data.get('Confidence')}\n"
            f"📝 *Summary:* {ai_data.get('Summary')}\n\n"
            f"🔗 [View Source]({notification['url']})"
        )

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")