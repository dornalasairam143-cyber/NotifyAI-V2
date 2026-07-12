import json
import logging
from typing import Dict, Any
from google import genai
from google.genai import types
from config import config

logger = logging.getLogger(__name__)

class AIClassifier:
    """Uses Google Gemini to intelligently classify and summarize notifications."""
    
    def __init__(self) -> None:
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_id = "gemini-2.5-flash"

    def analyze_notification(self, text: str, title: str) -> Dict[str, Any]:
        """Analyzes text and returns structured classification data."""
        if not config.GEMINI_API_KEY:
            logger.warning("No Gemini API key provided. Returning fallback data.")
            return self._fallback_response()

        prompt = f"""
        Analyze the following government/educational notification.
        Title: {title}
        Content Snippet: {text[:2000]}
        
        Extract the following information:
        1. Category (e.g., Counselling, Results, Admissions, Recruitment, Circular)
        2. Status (e.g., Registration Started, Result Declared, Postponed)
        3. Confidence (A percentage string, e.g., '95%')
        4. Summary (A crisp 1-2 sentence summary of the notification)
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "Category": {"type": "STRING"},
                            "Status": {"type": "STRING"},
                            "Confidence": {"type": "STRING"},
                            "Summary": {"type": "STRING"}
                        },
                        "required": ["Category", "Status", "Confidence", "Summary"]
                    },
                    temperature=0.1
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"AI Classification failed: {e}")
            return self._fallback_response()

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "Category": "Unclassified",
            "Status": "Update Available",
            "Confidence": "N/A",
            "Summary": "A new notification was detected but could not be classified via AI."
        }