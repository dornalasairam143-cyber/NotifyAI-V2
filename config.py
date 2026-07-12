"""
config.py
NotifyAI V2 Configuration
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:

    # ==========================================
    # Project Paths
    # ==========================================

    BASE_DIR = Path(__file__).resolve().parent

    CORE_DIR = BASE_DIR / "core"

    DATA_DIR = BASE_DIR / "data"

    CACHE_DIR = DATA_DIR / "cache"

    LOG_DIR = DATA_DIR / "logs"

    TEST_DIR = BASE_DIR / "tests"

    DB_PATH = DATA_DIR / "notify.db"

    EXCEL_PATH = BASE_DIR / "articles.xlsx"

    # ==========================================
    # Telegram
    # ==========================================

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # ==========================================
    # Gemini AI
    # ==========================================

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    GEMINI_MODEL = "gemini-2.5-flash"

    # ==========================================
    # Website Scanner
    # ==========================================

    MAX_WORKERS = 20

    REQUEST_TIMEOUT = 20

    RETRY_COUNT = 3

    CHECK_INTERVAL = 300

    USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )

    # ==========================================
    # Logging
    # ==========================================

    LOG_LEVEL = "INFO"

    LOG_FILE = LOG_DIR / "notify.log"

    # ==========================================
    # Excel
    # ==========================================

    REQUIRED_COLUMNS = [
        "Article Name",
        "Keywords",
        "Official Website",
        "Category",
        "Enabled"
    ]


config = Config()

# ==========================================
# Create Required Folders
# ==========================================

config.DATA_DIR.mkdir(parents=True, exist_ok=True)

config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

config.LOG_DIR.mkdir(parents=True, exist_ok=True)

config.TEST_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# Startup Information
# ==========================================

print("=" * 60)
print("NotifyAI V2 Configuration")
print("=" * 60)

print("Project :", config.BASE_DIR)
print("Database:", config.DB_PATH)
print("Excel   :", config.EXCEL_PATH)

if config.EXCEL_PATH.exists():
    print("Articles: FOUND")
else:
    print("Articles: NOT FOUND (articles.xlsx missing)")

print("=" * 60)