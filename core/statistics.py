"""
NotifyAI V4 - Statistics Module
Provides the StatisticsEngine class to compute, aggregate, and retrieve
detailed daily, weekly, monthly, database, runtime, and scan statistics.
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Union

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class StatisticsEngine:
    """
    Computes and aggregates statistical data across the NotifyAI V4 system,
    interacting with the main database, notification database, and dashboard.
    """

    def __init__(self, database: Any, notification_db: Any, dashboard: Any) -> None:
        """
        Initializes the StatisticsEngine.

        Args:
            database (Any): Instance of the main Database.
            notification_db (Any): Instance of the NotificationDatabase.
            dashboard (Any): Instance of the Dashboard module.
        """
        self.db = database
        self.notification_db = notification_db
        self.dashboard = dashboard

    def _execute_scalar(self, db_instance: Any, query: str, default: Union[int, float] = 0) -> Union[int, float]:
        """
        Safely executes a scalar SQLite query, returning a default value if it fails.
        This handles potential schema variations gracefully without crashing.

        Args:
            db_instance (Any): The database instance containing a valid 'conn' attribute.
            query (str): The SQL query string.
            default (Union[int, float]): Default value if result is None or error occurs.

        Returns:
            Union[int, float]: The scalar result of the query.
        """
        if not hasattr(db_instance, 'conn') or db_instance.conn is None:
            return default

        try:
            cursor = db_instance.conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result[0] is not None:
                # Ensure the return type matches the default type loosely
                return type(default)(result[0])
            return default
        except sqlite3.Error as e:
            logger.debug(f"Query failed (often due to schema updates): {query} -> {e}")
            return default
        except Exception as e:
            logger.error(f"Unexpected error executing scalar query: {e}")
            return default

    def get_daily_statistics(self) -> Dict[str, Any]:
        """
        Retrieves statistics for the current day.

        Returns:
            Dict[str, Any]: Daily statistics metrics.
        """
        logger.info("Generating daily statistics.")
        try:
            date_str = datetime.utcnow().strftime('%Y-%m-%d')
            
            return {
                "date": date_str,
                "articles": self._execute_scalar(self.db, "SELECT COUNT(*) FROM articles", 0),
                "active_articles": self._execute_scalar(self.db, "SELECT COUNT(*) FROM articles WHERE is_active = 1", 0),
                "notifications": self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications", 0),
                "new_notifications": self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications WHERE date(detected_date) = date('now')", 0),
                "duplicates": self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status = 'DUPLICATE' AND date(timestamp) = date('now')", 0),
                "telegram_sent": self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications WHERE status = 'Sent' AND date(detected_date) = date('now')", 0),
                "failed_scans": self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status LIKE 'FAILED%' AND date(timestamp) = date('now')", 0),
                "successful_scans": self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status = 'SUCCESS' AND date(timestamp) = date('now')", 0),
                "runtime": round(self._execute_scalar(self.db, "SELECT SUM(response_time) FROM scan_logs WHERE date(timestamp) = date('now')", 0.0), 2)
            }
        except Exception as e:
            logger.error(f"Failed to generate daily statistics: {e}")
            return {
                "date": datetime.utcnow().strftime('%Y-%m-%d'),
                "articles": 0, "active_articles": 0, "notifications": 0, "new_notifications": 0,
                "duplicates": 0, "telegram_sent": 0, "failed_scans": 0, "successful_scans": 0, "runtime": 0.0
            }

    def get_weekly_statistics(self) -> Dict[str, Any]:
        """
        Retrieves statistics for the current week (last 7 days).

        Returns:
            Dict[str, Any]: Weekly statistics metrics.
        """
        logger.info("Generating weekly statistics.")
        try:
            week_str = datetime.utcnow().strftime('%Y-W%W')
            
            return {
                "week": week_str,
                "articles": self._execute_scalar(self.db, "SELECT COUNT(*) FROM articles WHERE is_active = 1", 0),
                "notifications": self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications WHERE date(detected_date) >= date('now', '-7 days')", 0),
                "telegram": self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications WHERE status = 'Sent' AND date(detected_date) >= date('now', '-7 days')", 0),
                "failed": self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status LIKE 'FAILED%' AND date(timestamp) >= date('now', '-7 days')", 0),
                "runtime": round(self._execute_scalar(self.db, "SELECT SUM(response_time) FROM scan_logs WHERE date(timestamp) >= date('now', '-7 days')", 0.0), 2)
            }
        except Exception as e:
            logger.error(f"Failed to generate weekly statistics: {e}")
            return {"week": datetime.utcnow().strftime('%Y-W%W'), "articles": 0, "notifications": 0, "telegram": 0, "failed": 0, "runtime": 0.0}

    def get_monthly_statistics(self) -> Dict[str, Any]:
        """
        Retrieves statistics for the current month.

        Returns:
            Dict[str, Any]: Monthly statistics metrics.
        """
        logger.info("Generating monthly statistics.")
        try:
            month_str = datetime.utcnow().strftime('%Y-%m')
            
            return {
                "month": month_str,
                "articles": self._execute_scalar(self.db, "SELECT COUNT(*) FROM articles WHERE is_active = 1", 0),
                "notifications": self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications WHERE strftime('%Y-%m', detected_date) = strftime('%Y-%m', 'now')", 0),
                "telegram": self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications WHERE status = 'Sent' AND strftime('%Y-%m', detected_date) = strftime('%Y-%m', 'now')", 0),
                "failed": self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status LIKE 'FAILED%' AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')", 0),
                "runtime": round(self._execute_scalar(self.db, "SELECT SUM(response_time) FROM scan_logs WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')", 0.0), 2)
            }
        except Exception as e:
            logger.error(f"Failed to generate monthly statistics: {e}")
            return {"month": datetime.utcnow().strftime('%Y-%m'), "articles": 0, "notifications": 0, "telegram": 0, "failed": 0, "runtime": 0.0}

    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Retrieves physical database sizes and general row counts.

        Returns:
            Dict[str, Any]: Database statistics metrics.
        """
        logger.info("Generating database statistics.")
        try:
            db_size_bytes = 0
            if hasattr(self.db, 'db_path') and os.path.exists(self.db.db_path):
                db_size_bytes += os.path.getsize(self.db.db_path)
            if hasattr(self.notification_db, 'db_path') and os.path.exists(self.notification_db.db_path):
                db_size_bytes += os.path.getsize(self.notification_db.db_path)
                
            db_size_mb = f"{db_size_bytes / (1024 * 1024):.2f} MB"
            
            main_tables = self._execute_scalar(self.db, "SELECT COUNT(*) FROM sqlite_master WHERE type='table'", 0)
            notif_tables = self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM sqlite_master WHERE type='table'", 0)
            
            # Row approximation combining major known tables
            rows_scan_logs = self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs", 0)
            rows_articles = self._execute_scalar(self.db, "SELECT COUNT(*) FROM articles", 0)
            rows_notifications = self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications", 0)
            total_rows = rows_scan_logs + rows_articles + rows_notifications

            return {
                "database_size": db_size_mb,
                "tables": main_tables + notif_tables,
                "rows": total_rows,
                "notifications": rows_notifications,
                "articles": rows_articles
            }
        except Exception as e:
            logger.error(f"Failed to generate database statistics: {e}")
            return {"database_size": "0.00 MB", "tables": 0, "rows": 0, "notifications": 0, "articles": 0}

    def get_runtime_statistics(self) -> Dict[str, Any]:
        """
        Retrieves system performance and processing time statistics.
        Gracefully handles schemas missing granular time columns by defaulting to 0.0.

        Returns:
            Dict[str, Any]: Runtime statistics metrics.
        """
        logger.info("Generating runtime statistics.")
        try:
            return {
                "average_scan_time": round(self._execute_scalar(self.db, "SELECT AVG(response_time) FROM scan_logs", 0.0), 3),
                "fastest_scan": round(self._execute_scalar(self.db, "SELECT MIN(response_time) FROM scan_logs", 0.0), 3),
                "slowest_scan": round(self._execute_scalar(self.db, "SELECT MAX(response_time) FROM scan_logs", 0.0), 3),
                "average_ai_time": round(self._execute_scalar(self.db, "SELECT AVG(ai_time) FROM scan_logs", 0.0), 3),
                "average_pdf_time": round(self._execute_scalar(self.db, "SELECT AVG(pdf_time) FROM scan_logs", 0.0), 3),
                "average_download_time": round(self._execute_scalar(self.db, "SELECT AVG(download_time) FROM scan_logs", 0.0), 3)
            }
        except Exception as e:
            logger.error(f"Failed to generate runtime statistics: {e}")
            return {
                "average_scan_time": 0.0, "fastest_scan": 0.0, "slowest_scan": 0.0,
                "average_ai_time": 0.0, "average_pdf_time": 0.0, "average_download_time": 0.0
            }

    def get_scan_statistics(self) -> Dict[str, Any]:
        """
        Calculates rates and percentages of scan successes, failures, and discoveries.

        Returns:
            Dict[str, Any]: Scan metrics including success and failure rates.
        """
        logger.info("Generating scan statistics.")
        try:
            total_scans = self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs", 0)
            
            if total_scans == 0:
                return {
                    "success_rate": 0.0,
                    "failure_rate": 0.0,
                    "duplicate_rate": 0.0,
                    "notification_rate": 0.0
                }

            successful_scans = self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status = 'SUCCESS'", 0)
            failed_scans = self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status LIKE 'FAILED%'", 0)
            duplicates = self._execute_scalar(self.db, "SELECT COUNT(*) FROM scan_logs WHERE status = 'DUPLICATE'", 0)
            total_notifications = self._execute_scalar(self.notification_db, "SELECT COUNT(*) FROM notifications", 0)

            return {
                "success_rate": round((successful_scans / total_scans) * 100, 2),
                "failure_rate": round((failed_scans / total_scans) * 100, 2),
                "duplicate_rate": round((duplicates / total_scans) * 100, 2),
                # Notification rate represents notifications found per scan total
                "notification_rate": round((total_notifications / total_scans) * 100, 2) if total_scans > 0 else 0.0
            }
        except Exception as e:
            logger.error(f"Failed to generate scan statistics: {e}")
            return {"success_rate": 0.0, "failure_rate": 0.0, "duplicate_rate": 0.0, "notification_rate": 0.0}