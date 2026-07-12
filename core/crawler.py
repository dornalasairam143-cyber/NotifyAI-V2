import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Tuple, Optional
from config import config

class Crawler:
    """Robust web crawler with connection pooling, retries, and timeouts."""
    
    def __init__(self) -> None:
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Builds a robust requests Session with automatic retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": config.USER_AGENT})
        return session

    def fetch(self, url: str) -> Tuple[Optional[bytes], int, str, float]:
        """
        Fetches a URL and returns (content_bytes, status_code, content_type, response_time).
        """
        start_time = time.time()
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            elapsed = time.time() - start_time
            content_type = response.headers.get("Content-Type", "").lower()
            return response.content, response.status_code, content_type, elapsed
        except requests.RequestException as e:
            elapsed = time.time() - start_time
            return None, 0, "", elapsed