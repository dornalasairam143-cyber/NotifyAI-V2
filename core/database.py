import sqlite3
import pandas as pd
from typing import List, Dict, Optional
from config import config

class Database:
    """Handles SQLite database operations and state management."""
    
    def __init__(self) -> None:
        self.db_path = config.DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes database tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_name TEXT,
                    keywords TEXT,
                    official_website TEXT,
                    category TEXT,
                    enabled INTEGER DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    url TEXT UNIQUE,
                    title TEXT,
                    hash TEXT UNIQUE,
                    detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(article_id) REFERENCES articles(id)
                );
                
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website TEXT,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time_ms INTEGER,
                    status TEXT,
                    error TEXT
                );
            """)
            conn.commit()

    def sync_excel_to_db(self) -> None:
        """Reads articles.xlsx and synchronizes it with the SQLite database."""
        if not config.EXCEL_PATH.exists():
            return

        df = pd.read_excel(config.EXCEL_PATH)
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles") # Refresh from Excel
            for _, row in df.iterrows():
                if int(row.get('enabled', 1)) == 1:
                    cursor.execute("""
                        INSERT INTO articles (article_name, keywords, official_website, category, enabled)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(row.get('article_name', '')),
                        str(row.get('keywords', '')),
                        str(row.get('official_website', '')),
                        str(row.get('category', '')),
                        1
                    ))
            conn.commit()

    def get_active_articles(self) -> List[Dict]:
        """Retrieves all enabled articles."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE enabled = 1")
            return [dict(row) for row in cursor.fetchall()]

    def is_notification_new(self, url: str, hash_val: str) -> bool:
        """Checks if a notification is new based on URL or content Hash."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM notifications WHERE url = ? OR hash = ?", (url, hash_val))
            return cursor.fetchone() is None

    def save_notification(self, article_id: int, url: str, title: str, hash_val: str) -> None:
        """Saves a newly discovered notification to state."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO notifications (article_id, url, title, hash)
                    VALUES (?, ?, ?, ?)
                """, (article_id, url, title, hash_val))
                conn.commit()
            except sqlite3.IntegrityError:
                pass # Already exists

    def log_scan(self, website: str, response_time: int, status: str, error: str = "") -> None:
        """Logs crawl statistics and errors."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (website, response_time_ms, status, error)
                VALUES (?, ?, ?, ?)
            """, (website, response_time, status, error))
            conn.commit()