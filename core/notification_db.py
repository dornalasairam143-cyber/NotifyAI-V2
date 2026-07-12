"""
NotifyAI V2 - Notification Database Module
Provides the NotificationDatabase class for managing notification records using SQLite.
"""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# Assuming config.py is in the same directory or Python path
from config import config

DB_PATH = config.DB_PATH

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class NotificationDatabase:
    """
    Handles SQLite database operations for NotifyAI V2 notifications.
    """

    def __init__(self, db_path: str = DB_PATH) -> None:
        """
        Initializes the database connection and ensures tables are created.
        
        Args:
            db_path (str): The file path to the SQLite database.
        """
        self.db_path = db_path
        try:
            # Using check_same_thread=False is often required in multi-threaded environments (like web frameworks)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Use Row factory to return query results as dictionaries
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Successfully connected to SQLite database at '{self.db_path}'")
            
            # Automatically create tables if they do not exist
            self.create_tables()
            
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database at '{self.db_path}': {e}")
            raise

    def create_tables(self) -> bool:
        """
        Creates the 'notifications' table if it does not already exist.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article TEXT,
            title TEXT,
            url TEXT UNIQUE,
            published_date TEXT,
            detected_date TEXT,
            summary TEXT,
            category TEXT,
            status TEXT,
            confidence REAL
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_sql)
            self.conn.commit()
            logger.debug("Table 'notifications' verified/created successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            return False

    def notification_exists(self, url: str) -> bool:
        """
        Checks if a notification with the given URL already exists.
        
        Args:
            url (str): The unique URL of the notification.
            
        Returns:
            bool: True if it exists, False otherwise.
        """
        query = "SELECT 1 FROM notifications WHERE url = ? LIMIT 1;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking if notification exists for URL '{url}': {e}")
            return False

    def save_notification(
        self, 
        article: str, 
        title: str, 
        url: str, 
        published_date: str, 
        summary: str, 
        category: str, 
        status: str, 
        confidence: float
    ) -> bool:
        """
        Saves a new notification to the database. Automatically generates the detected_date.
        
        Args:
            article (str): The source article or text.
            title (str): Title of the notification.
            url (str): Unique URL.
            published_date (str): Date the original article was published.
            summary (str): Summarized text.
            category (str): Classification category.
            status (str): Current processing or delivery status.
            confidence (float): Confidence score of the detection/categorization.
            
        Returns:
            bool: True if the record was saved successfully, False if it failed (e.g., duplicate URL).
        """
        detected_date = datetime.now(timezone.utc).isoformat()
        
        query = """
        INSERT INTO notifications (
            article, title, url, published_date, detected_date, 
            summary, category, status, confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        parameters = (
            article, title, url, published_date, detected_date,
            summary, category, status, confidence
        )
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            self.conn.commit()
            logger.info(f"Successfully saved notification for URL: '{url}'")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Notification with URL '{url}' already exists (IntegrityError).")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error saving notification for URL '{url}': {e}")
            return False

    def get_notification(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single notification by its URL.
        
        Args:
            url (str): The unique URL to look up.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the notification, or None if not found/error.
        """
        query = "SELECT * FROM notifications WHERE url = ?;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (url,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving notification for URL '{url}': {e}")
            return None

    def get_all_notifications(self) -> List[Dict[str, Any]]:
        """
        Retrieves all notifications from the database.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a notification row.
        """
        query = "SELECT * FROM notifications ORDER BY detected_date DESC;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all notifications: {e}")
            return []

    def delete_notification(self, url: str) -> bool:
        """
        Deletes a notification from the database by its URL.
        
        Args:
            url (str): The unique URL of the notification to delete.
            
        Returns:
            bool: True if the deletion was successful (even if it didn't exist), False on error.
        """
        query = "DELETE FROM notifications WHERE url = ?;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (url,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted notification with URL: '{url}'")
            else:
                logger.debug(f"No notification found to delete for URL: '{url}'")
                
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting notification for URL '{url}': {e}")
            return False

    def clear_notifications(self) -> bool:
        """
        Deletes all notifications from the database.
        
        Returns:
            bool: True if successful, False on error.
        """
        query = "DELETE FROM notifications;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            logger.warning(f"Cleared all notifications. {cursor.rowcount} rows deleted.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error clearing notifications: {e}")
            return False

    def count_notifications(self) -> int:
        """
        Returns the total number of notifications in the database.
        
        Returns:
            int: The total count of rows, or 0 if an error occurs.
        """
        query = "SELECT COUNT(*) FROM notifications;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            logger.error(f"Error counting notifications: {e}")
            return 0

    def close(self) -> None:
        """
        Closes the database connection cleanly.
        """
        try:
            self.conn.close()
            logger.info("Database connection closed.")
        except sqlite3.Error as e:
            logger.error(f"Error closing the database connection: {e}")