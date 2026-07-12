"""
NotifyAI V3 - Dashboard Module
Provides the Dashboard class to aggregate, calculate, and display
system statistics from the main database and notification database.
"""

import os
import logging
import sqlite3
from typing import Dict, Any

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class Dashboard:
    """
    Dashboard for NotifyAI V3.
    Calculates and displays system performance, database health, and processing statistics.
    """

    def __init__(self, database: Any, notification_db: Any) -> None:
        """
        Initializes the Dashboard.

        Args:
            database (Any): Instance of the main Database class.
            notification_db (Any): Instance of the NotificationDatabase class.
        """
        self.db = database
        self.notification_db = notification_db

    def _execute_scalar_query(self, connection: sqlite3.Connection, query: str, default: Any = 0) -> Any:
        """
        Safely executes a scalar SQLite query and returns the first result.
        
        Args:
            connection (sqlite3.Connection): The SQLite connection object.
            query (str): The SQL query string.
            default (Any): The default value to return if the query fails or returns None.
            
        Returns:
            Any: The query result or the default value.
        """
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else default
        except sqlite3.Error as e:
            logger.debug(f"Dashboard query failed or table missing: {query} -> {e}")
            return default

    def get_statistics(self) -> Dict[str, Any]:
        """
        Aggregates operational statistics from both databases.

        Returns:
            Dict[str, Any]: A dictionary containing system statistics.
        """
        stats: Dict[str, Any] = {
            "articles": 0,
            "active_articles": 0,
            "notifications": 0,
            "new_today": 0,
            "duplicates": 0,
            "telegram_sent": 0,
            "failed_scans": 0,
            "successful_scans": 0,
            "last_scan": "N/A",
            "database_size": "0.00 MB",
            "average_scan_time": 0.0
        }

        # 1. Main DB queries
        if hasattr(self.db, "conn"):
            conn = self.db.conn
            stats["articles"] = self._execute_scalar_query(conn, "SELECT COUNT(*) FROM articles", 0)
            
            # Using is_active (assumed schema)
            stats["active_articles"] = self._execute_scalar_query(
                conn, "SELECT COUNT(*) FROM articles WHERE is_active = 1", stats["articles"]
            )
            
            stats["successful_scans"] = self._execute_scalar_query(
                conn, "SELECT COUNT(*) FROM scan_logs WHERE status = 'SUCCESS'", 0
            )
            
            stats["failed_scans"] = self._execute_scalar_query(
                conn, "SELECT COUNT(*) FROM scan_logs WHERE status LIKE 'FAILED%'", 0
            )
            
            stats["duplicates"] = self._execute_scalar_query(
                conn, "SELECT COUNT(*) FROM scan_logs WHERE status = 'DUPLICATE'", 0
            )
            
            # Try response_time in ms or fallback to response_time directly
            avg_time = self._execute_scalar_query(conn, "SELECT AVG(response_time_ms) FROM scan_logs", 0.0)
            if avg_time > 0:
                stats["average_scan_time"] = round(avg_time / 1000.0, 2)
            else:
                avg_time = self._execute_scalar_query(conn, "SELECT AVG(response_time) FROM scan_logs", 0.0)
                stats["average_scan_time"] = round(avg_time, 2)
                
            # Attempt to fetch last scan time
            last_scan = self._execute_scalar_query(conn, "SELECT MAX(timestamp) FROM scan_logs", "N/A")
            if last_scan == "N/A":
                last_scan = self._execute_scalar_query(conn, "SELECT MAX(scanned_at) FROM scan_logs", "N/A")
            stats["last_scan"] = last_scan

        # 2. Notification DB queries
        if hasattr(self.notification_db, "conn"):
            conn = self.notification_db.conn
            stats["notifications"] = self._execute_scalar_query(
                conn, "SELECT COUNT(*) FROM notifications", 0
            )
            
            stats["new_today"] = self._execute_scalar_query(
                conn, "SELECT COUNT(*) FROM notifications WHERE date(detected_date) = date('now')", 0
            )
            
            # Assuming 'Sent' is a status representing a dispatched Telegram message
            stats["telegram_sent"] = self._execute_scalar_query(
                conn, "SELECT COUNT(*) FROM notifications WHERE status = 'Sent' AND date(detected_date) = date('now')", 
                stats["new_today"]  # Fallback assumption if exact status tracking is unavailable
            )

        # 3. Calculate physical database sizes
        try:
            size_bytes = 0
            if hasattr(self.db, "db_path") and os.path.exists(self.db.db_path):
                size_bytes += os.path.getsize(self.db.db_path)
            if hasattr(self.notification_db, "db_path") and os.path.exists(self.notification_db.db_path):
                size_bytes += os.path.getsize(self.notification_db.db_path)
                
            stats["database_size"] = f"{size_bytes / (1024 * 1024):.2f} MB"
        except Exception as e:
            logger.warning(f"Error calculating database sizes: {e}")

        return stats

    def print_dashboard(self) -> None:
        """
        Prints the system statistics in a cleanly formatted console dashboard.
        """
        try:
            stats = self.get_statistics()
            
            dashboard_text = (
                "\n"
                "==================================================\n"
                "NotifyAI Dashboard\n"
                "==================================================\n"
                f"Articles                  : {stats.get('active_articles', 0)} / {stats.get('articles', 0)}\n"
                f"Notifications             : {stats.get('notifications', 0)}\n"
                f"Today's Notifications     : {stats.get('new_today', 0)}\n"
                f"Today's Telegram Messages : {stats.get('telegram_sent', 0)}\n"
                f"Duplicate Notifications   : {stats.get('duplicates', 0)}\n"
                f"Successful Scans          : {stats.get('successful_scans', 0)}\n"
                f"Failed Scans              : {stats.get('failed_scans', 0)}\n"
                f"Average Scan Time         : {stats.get('average_scan_time', 0.0)}s\n"
                f"Database Size             : {stats.get('database_size', '0.00 MB')}\n"
                f"Last Scan                 : {stats.get('last_scan', 'N/A')}\n"
                "=================================================="
            )
            
            print(dashboard_text)
            logger.info("Dashboard printed successfully.")
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard output: {e}")