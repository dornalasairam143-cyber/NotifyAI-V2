"""
NotifyAI V4.2 Professional
Engine
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from core.database import Database
from core.notification_db import NotificationDatabase
from core.discovery import WebsiteDiscovery
from core.crawler import Crawler
from core.parser import Parser
from core.matcher import Matcher
from core.ai_classifier import AIClassifier
from core.notifier import TelegramNotifier
from core.dashboard import Dashboard
from core.statistics import StatisticsEngine
from core.report_generator import ReportGenerator
from core.daily_report import DailyReport

logger = logging.getLogger(__name__)


class NotifyEngine:
    """
    Main application engine.

    Coordinates every module of NotifyAI.
    """

    def __init__(self):

        logger.info("Initializing NotifyAI Engine...")

        self.database = Database()

        self.notification_db = NotificationDatabase()

        self.discovery = WebsiteDiscovery()

        self.crawler = Crawler()

        self.parser = Parser()

        self.matcher = Matcher()

        self.ai = AIClassifier()

        self.telegram = TelegramNotifier()

        self.dashboard = Dashboard(
            self.database,
            self.notification_db,
        )

        self.statistics = StatisticsEngine(
            self.database,
            self.notification_db,
            self.dashboard,
        )

        self.report_generator = ReportGenerator(
            self.dashboard,
            self.statistics,
            self.notification_db,
        )

        self.daily_report = DailyReport(
            self.dashboard,
            self.statistics,
            self.report_generator,
            self.telegram,
        )

        logger.info("NotifyAI Engine Ready.")

    # -------------------------------------------------

    def health(self) -> Dict:

        return {

            "database": self.database is not None,

            "notification_db": self.notification_db is not None,

            "crawler": self.crawler is not None,

            "parser": self.parser is not None,

            "matcher": self.matcher is not None,

            "ai": self.ai is not None,

            "telegram": self.telegram is not None,

            "dashboard": self.dashboard is not None,

            "statistics": self.statistics is not None,

            "reports": self.report_generator is not None,

        }

    # -------------------------------------------------

    def version(self):

        return "NotifyAI V4.2 Professional"

    # -------------------------------------------------

    def startup(self):

        logger.info("Starting NotifyAI Engine...")
            # -------------------------------------------------
    # Scan Single Website
    # -------------------------------------------------

    def scan_website(
        self,
        article: Dict,
    ) -> int:
        """
        Scan a single website for new notifications.

        Returns:
            Number of new notifications found.
        """

        website = article.get("official_website", "").strip()

        if not website:
            logger.warning("Website URL missing.")
            return 0

        logger.info("Scanning: %s", website)

        # -------------------------------------------------
        # Discover Links
        # -------------------------------------------------

        links = self.discovery.discover(website)

        logger.info(
            "Discovered %s candidate links.",
            len(links),
        )

        new_notifications = 0

        # -------------------------------------------------
        # Process Links
        # -------------------------------------------------

        for item in links:

            try:

                title = item.get("title", "").strip()

                url = item.get("url", "").strip()

                if not url:
                    continue

                logger.info("Checking: %s", title)

                # ---------------------------------------------
                # Duplicate Check
                # ---------------------------------------------

                if self.notification_db.notification_exists(url):

                    logger.info("Already exists.")

                    continue

                # ---------------------------------------------
                # Download Page / PDF
                # ---------------------------------------------

                content, status, content_type, _ = self.crawler.fetch(url)

                if status != 200:

                    logger.warning(
                        "Failed to fetch %s",
                        url,
                    )

                    continue

                # ---------------------------------------------
                # Extract Text
                # ---------------------------------------------

                if "pdf" in content_type.lower():

                    text = self.parser.parse_pdf(content)

                else:

                    text = self.parser.parse_html(content)

                # ---------------------------------------------
                # AI Classification
                # ---------------------------------------------

                ai_result = self.ai.analyze_notification(
                    title=title,
                    content=text,
                )

                # ---------------------------------------------
                # Save Notification
                # ---------------------------------------------

                self.notification_db.add_notification(

                    article_id=article["id"],

                    title=title,

                    url=url,

                    content=text,

                    category=ai_result.get(
                        "category",
                        "Unknown",
                    ),

                    priority=ai_result.get(
                        "priority",
                        "Normal",
                    ),

                )

                # ---------------------------------------------
                # Telegram
                # ---------------------------------------------

                self.telegram.send_alert(

                    article_name=article["article_name"],

                    website=website,

                    notification={

                        "title": title,

                        "url": url,

                    },

                    ai_result=ai_result,

                )

                logger.info(
                    "New notification: %s",
                    title,
                )

                new_notifications += 1

            except Exception as exc:

                logger.exception(
                    "Error processing notification: %s",
                    exc,
                )

        return new_notifications

    # -------------------------------------------------
    # Scan All Websites
    # -------------------------------------------------

    def scan_all(self) -> Dict:
        """
        Scan every enabled website.
        """

        logger.info(
            "Loading active websites..."
        )

        articles = self.database.get_active_articles()

        logger.info(
            "%s websites loaded.",
            len(articles),
        )

        total_notifications = 0

        start = time.perf_counter()

        for article in articles:

            try:

                total_notifications += self.scan_website(
                    article
                )

            except Exception as exc:

                logger.exception(exc)

        elapsed = round(
            time.perf_counter() - start,
            2,
        )

        summary = {

            "websites": len(articles),

            "notifications": total_notifications,

            "elapsed": elapsed,

        }

        logger.info(summary)

        return summary
        # -------------------------------------------------
    # Update Dashboard
    # -------------------------------------------------

    def update_dashboard(self):
        """
        Refresh dashboard after a scan.
        """

        logger.info("Updating dashboard...")

        try:

            self.dashboard.refresh()

            logger.info("Dashboard updated successfully.")

        except Exception as exc:

            logger.exception(
                "Dashboard update failed: %s",
                exc,
            )

    # -------------------------------------------------
    # Update Statistics
    # -------------------------------------------------

    def update_statistics(self):
        """
        Recalculate project statistics.
        """

        logger.info("Updating statistics...")

        try:

            self.statistics.generate()

            logger.info("Statistics updated.")

        except Exception as exc:

            logger.exception(
                "Statistics failed: %s",
                exc,
            )

    # -------------------------------------------------
    # Generate Reports
    # -------------------------------------------------

    def generate_reports(self):
        """
        Generate all project reports.
        """

        logger.info("Generating reports...")

        try:

            self.report_generator.generate_html()

            self.report_generator.generate_excel()

            logger.info("Reports generated.")

        except Exception as exc:

            logger.exception(
                "Report generation failed: %s",
                exc,
            )

    # -------------------------------------------------
    # Daily Summary
    # -------------------------------------------------

    def send_daily_report(self):
        """
        Send daily summary.
        """

        logger.info("Generating daily report...")

        try:

            self.daily_report.send()

            logger.info("Daily report sent.")

        except Exception as exc:

            logger.exception(
                "Daily report failed: %s",
                exc,
            )

    # -------------------------------------------------
    # Health Check
    # -------------------------------------------------

    def health_check(self) -> Dict:
        """
        Return engine health.
        """

        return {

            "database": self.database is not None,

            "notification_db": self.notification_db is not None,

            "crawler": self.crawler is not None,

            "parser": self.parser is not None,

            "matcher": self.matcher is not None,

            "ai": self.ai is not None,

            "telegram": self.telegram is not None,

            "dashboard": self.dashboard is not None,

            "statistics": self.statistics is not None,

            "reports": self.report_generator is not None,

            "daily_report": self.daily_report is not None,

        }

    # -------------------------------------------------
    # Full Workflow
    # -------------------------------------------------

    def run(self) -> Dict:
        """
        Execute one complete NotifyAI cycle.
        """

        logger.info("=" * 70)
        logger.info("NotifyAI Scan Started")
        logger.info("=" * 70)

        summary = self.scan_all()

        self.update_dashboard()

        self.update_statistics()

        self.generate_reports()

        self.send_daily_report()

        logger.info("=" * 70)
        logger.info("NotifyAI Scan Finished")
        logger.info("=" * 70)

        return summary
        # -------------------------------------------------
    # Shutdown Engine
    # -------------------------------------------------

    def shutdown(self):
        """
        Gracefully shut down the NotifyAI engine.
        """

        logger.info("=" * 70)
        logger.info("Shutting down NotifyAI Engine...")
        logger.info("=" * 70)

        try:

            if hasattr(self.database, "close"):
                self.database.close()

            if hasattr(self.notification_db, "close"):
                self.notification_db.close()

            logger.info("All database connections closed.")

        except Exception as exc:

            logger.exception(
                "Shutdown error: %s",
                exc,
            )

    # -------------------------------------------------
    # Restart Engine
    # -------------------------------------------------

    def restart(self):
        """
        Restart the engine.
        """

        logger.info("Restarting NotifyAI Engine...")

        self.shutdown()

        time.sleep(2)

        self.__init__()

        logger.info("Restart complete.")

    # -------------------------------------------------
    # Engine Statistics
    # -------------------------------------------------

    def statistics(self) -> Dict:
        """
        Return engine statistics.
        """

        return {

            "version": self.version(),

            "health": self.health_check(),

            "database_records": (
                self.database.count_articles()
                if hasattr(self.database, "count_articles")
                else 0
            ),

            "notifications": (
                self.notification_db.count_notifications()
                if hasattr(self.notification_db, "count_notifications")
                else 0
            ),

        }

    # -------------------------------------------------
    # Context Manager
    # -------------------------------------------------

    def __enter__(self):

        self.startup()

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):

        self.shutdown()

    # -------------------------------------------------
    # String Representation
    # -------------------------------------------------

    def __repr__(self):

        return (
            f"<NotifyEngine "
            f"version='{self.version()}'>"
        )


# =====================================================
# Module Exports
# =====================================================

__all__ = [
    "NotifyEngine",
]

logger.info(
    "NotifyAI Engine Loaded Successfully."
)
