import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from config import config
from core.database import Database
from core.notification_db import NotificationDatabase
from core.crawler import Crawler
from core.parser import Parser
from core.pdf_reader import extract_text_from_pdf
from core.ai_classifier import AIClassifier
from core.notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("NotifyAI-V2")

class NotifyAI:
    def __init__(self) -> None:
        self.db = Database()
        self.notification_db = NotificationDatabase()
        self.crawler = Crawler()
        self.parser = Parser()
        self.ai = AIClassifier()
        self.notifier = TelegramNotifier()

    def process_website(self, article: dict) -> None:
        website_url = article.get('official_website', '')
        article_name = article.get('article_name', 'Unknown')
        
        if not website_url:
            return

        logger.info(f"Scanning website: {website_url}")
        
        try:
            content, status, c_type, response_time = self.crawler.fetch(website_url)
            logger.info("Website fetched")
            self.db.log_scan(website_url, int(response_time * 1000), "SUCCESS" if status == 200 else f"FAILED:{status}")
        except Exception as e:
            logger.error(f"Crawler failed on {website_url}: {e}")
            return

        if status != 200 or not content:
            return

        try:
            notifications = self.parser.extract_links(website_url, content)
        except Exception as e:
            logger.error(f"Parser failed on {website_url}: {e}")
            return

        for notif in notifications:
            try:
                url = notif.get('url')
                title = notif.get('title', 'Unknown Title')
                published_date = notif.get('published_date', '')

                if not url:
                    continue

                logger.info(f"Notification detected: {title}")

                try:
                    exists = self.notification_db.notification_exists(url)
                except Exception as e:
                    logger.error(f"SQLite error checking existence for {url}: {e}")
                    continue

                if exists:
                    logger.info("Already exists")
                    logger.info("Skipping")
                    continue

                try:
                    sub_content, sub_status, sub_type, _ = self.crawler.fetch(url)
                except Exception as e:
                    logger.error(f"Crawler failed to fetch notification {url}: {e}")
                    continue

                if sub_status != 200 or not sub_content:
                    logger.error(f"Failed to fetch content for {url} (Status: {sub_status})")
                    continue

                text_content = ""
                if "pdf" in str(sub_type).lower():
                    logger.info("Downloading PDF")
                    try:
                        text_content = extract_text_from_pdf(sub_content)
                    except Exception as e:
                        logger.error(f"PDF extraction failed for {url}: {e}")
                        continue
                else:
                    try:
                        text_content = BeautifulSoup(sub_content, "html.parser").get_text(separator=" ", strip=True)
                    except Exception as e:
                        logger.error(f"HTML parsing failed for {url}: {e}")
                        continue

                logger.info("Running AI")
                try:
                    ai_result = self.ai.analyze_notification(text_content, title)
                    summary = ai_result.get('summary', '')
                    category = ai_result.get('category', 'Unknown')
                    status_val = ai_result.get('status', 'Pending')
                    confidence = float(ai_result.get('confidence', 0.0))
                except Exception as e:
                    logger.error(f"AI classification failed for {url}: {e}")
                    continue

                logger.info("Sending Telegram")
                try:
                    self.notifier.send_alert(article_name, website_url, notif, ai_result)
                except Exception as e:
                    logger.error(f"Telegram notification failed for {url}: {e}")
                    continue

                logger.info("Saving Database")
                try:
                    self.notification_db.save_notification(
                        article=article_name,
                        title=title,
                        url=url,
                        published_date=published_date,
                        summary=summary,
                        category=category,
                        status=status_val,
                        confidence=confidence
                    )
                except Exception as e:
                    logger.error(f"SQLite save failed for {url}: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error processing notification {notif.get('url')}: {e}")
                continue

    def run(self) -> None:
        logger.info("Starting workflow")
        
        try:
            self.db.sync_excel_to_db()
            articles = self.db.get_active_articles()
        except Exception as e:
            logger.error(f"Failed to sync or fetch articles: {e}")
            return

        if not articles:
            logger.warning("No active articles found.")
            return

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = {executor.submit(self.process_website, article): article for article in articles}
            for future in as_completed(futures):
                article = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Unhandled exception in thread for {article.get('official_website')}: {e}")

        logger.info("Completed")

if __name__ == "__main__":
    app = NotifyAI()
    app.run()