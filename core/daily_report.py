"""
NotifyAI V4 - Daily Report Module
Provides the DailyReport class to orchestrate the generation, saving, 
and dispatching of a high-level daily markdown summary to Telegram.
"""

import os
import logging
from datetime import datetime
from typing import Any, Optional

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class DailyReport:
    """
    Generates, saves, and dispatches daily operational summaries.
    Coordinates between Dashboard, StatisticsEngine, ReportGenerator, and TelegramNotifier.
    """

    def __init__(
        self,
        dashboard: Any,
        statistics_engine: Any,
        report_generator: Any,
        telegram_notifier: Any
    ) -> None:
        """
        Initializes the DailyReport module.

        Args:
            dashboard (Any): Instance of Dashboard.
            statistics_engine (Any): Instance of StatisticsEngine.
            report_generator (Any): Instance of ReportGenerator.
            telegram_notifier (Any): Instance of TelegramNotifier.
        """
        self.dashboard = dashboard
        self.stats_engine = statistics_engine
        self.report_generator = report_generator
        self.notifier = telegram_notifier
        
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)

    def build_report(self) -> str:
        """
        Compiles data from StatisticsEngine and Dashboard to build a 
        beautiful Telegram-compatible Markdown string.

        Returns:
            str: The formatted Markdown report string.
        """
        logger.info("Building daily summary report.")
        try:
            daily_stats = self.stats_engine.get_daily_statistics()
            db_stats = self.stats_engine.get_database_statistics()
            
            date_str = daily_stats.get("date", datetime.utcnow().strftime('%Y-%m-%d'))
            successful = int(daily_stats.get("successful_scans", 0))
            failed = int(daily_stats.get("failed_scans", 0))
            total_scanned = successful + failed
            
            report = (
                "📊 *NotifyAI Daily Report*\n\n"
                f"📅 *Date:* {date_str}\n"
                f"🌐 *Websites Scanned:* {total_scanned}\n"
                f"✅ *Successful:* {successful}\n"
                f"❌ *Failed:* {failed}\n\n"
                f"🔔 *Notifications (Total):* {daily_stats.get('notifications', 0)}\n"
                f"🆕 *New Notifications (Today):* {daily_stats.get('new_notifications', 0)}\n"
                f"♻️ *Duplicate Notifications:* {daily_stats.get('duplicates', 0)}\n"
                f"📨 *Telegram Messages Sent:* {daily_stats.get('telegram_sent', 0)}\n\n"
                f"⏱ *Total Runtime:* {daily_stats.get('runtime', 0.0)}s\n"
                f"💾 *Database Size:* {db_stats.get('database_size', '0.00 MB')}\n"
            )
            return report
            
        except Exception as e:
            logger.error(f"Failed to build daily report string: {e}")
            return (
                "⚠️ *NotifyAI Daily Report Error*\n"
                "An error occurred while compiling the daily statistics.\n"
                f"Details: {str(e)}"
            )

    def send_daily_report(self) -> bool:
        """
        Builds the daily report and dispatches it via the TelegramNotifier.
        
        Returns:
            bool: True if dispatched successfully, False otherwise.
        """
        logger.info("Dispatching daily report via Telegram.")
        try:
            report_text = self.build_report()
            
            # Assuming the TelegramNotifier exposes a generic send_message method
            # If the exact method name differs in your implementation, adjust accordingly.
            if hasattr(self.notifier, "send_message"):
                self.notifier.send_message(report_text)
            else:
                logger.warning("TelegramNotifier lacks a 'send_message' method. Attempting fallback notification.")
                # Fallback to standard alert signature if custom message sender is missing
                self.notifier.send_alert(
                    article_name="NotifyAI System",
                    website_url="System Dashboard",
                    notification_data={"title": "Daily Summary Report", "url": ""},
                    ai_result={"summary": report_text, "category": "System", "status": "Info", "confidence": 1.0}
                )
                
            logger.info("Daily report dispatched successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Error dispatching daily report to Telegram: {e}")
            return False

    def save_daily_report(self) -> bool:
        """
        Builds the daily report and saves it locally as a text file.
        
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        filepath = os.path.join(self.output_dir, "daily_summary.txt")
        logger.info(f"Saving daily report locally to {filepath}")
        
        try:
            report_text = self.build_report()
            
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(report_text)
                
            logger.info("Daily report saved successfully.")
            return True
            
        except IOError as e:
            logger.error(f"File I/O error saving daily report: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving daily report: {e}")
            return False