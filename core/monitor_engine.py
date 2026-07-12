"""
NotifyAI V3 - Monitor Engine Module
Orchestrates the continuous monitoring workflow by integrating Discovery, Ranking, 
Crawling, Parsing, AI Classification, and Notification components.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from bs4 import BeautifulSoup

# Assuming core.pdf_reader is available from previous project structure
try:
    from core.pdf_reader import extract_text_from_pdf
except ImportError:
    # Fallback if module is not found in the exact path
    def extract_text_from_pdf(content: bytes) -> str:
        return "PDF Text Extraction Not Implemented/Available."

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class MonitorEngine:
    """
    Executes the end-to-end monitoring workflow for a given article/website.
    Discovers links, ranks them using AI, extracts notifications, checks for duplicates,
    processes content, and sends alerts.
    """

    def __init__(
        self,
        crawler: Any,
        parser: Any,
        discovery: Any,
        ranker: Any,
        notification_db: Any,
        ai_classifier: Any,
        notifier: Any
    ) -> None:
        """
        Initializes the MonitorEngine with all required dependencies.
        """
        self.crawler = crawler
        self.parser = parser
        self.discovery = discovery
        self.ranker = ranker
        self.db = notification_db
        self.ai = ai_classifier
        self.notifier = notifier
        
        self.max_workers = 5
        self.max_retries = 3

    def monitor(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution workflow for monitoring an article's official website.
        
        Args:
            article (Dict[str, Any]): Dictionary containing 'article_name' and 'official_website'.
            
        Returns:
            Dict[str, Any]: Execution statistics.
        """
        start_time = time.time()
        base_url = article.get("official_website", "")
        article_name = article.get("article_name", "Unknown")
        
        stats = {
            "pages": 0,
            "notifications": 0,
            "new": 0,
            "duplicates": 0,
            "errors": 0,
            "time": 0.0
        }

        if not base_url:
            logger.error("No official_website provided in article.")
            stats["errors"] += 1
            return stats

        logger.info(f"Starting monitoring workflow for: {article_name} ({base_url})")

        try:
            # 2. Discover website pages
            discovered_links = self.discovery.discover(base_url)
            
            # 3. AI Rank Links
            ranked_links = self.ranker.rank_links(discovered_links)
            
            # 4. Monitor only Top 10 (handled by LinkRanker max limits, but we ensure it here)
            target_links = ranked_links[:10]
            stats["pages"] = len(target_links)
            
            if not target_links:
                logger.warning(f"No high-value links found to monitor for {base_url}")
                stats["time"] = round(time.time() - start_time, 2)
                return stats

            # Concurrently process the top ranked pages
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._process_monitored_page, link, article_name): link 
                    for link in target_links
                }
                
                for future in as_completed(futures):
                    try:
                        page_stats = future.result()
                        # Aggregate statistics
                        stats["notifications"] += page_stats.get("notifications", 0)
                        stats["new"] += page_stats.get("new", 0)
                        stats["duplicates"] += page_stats.get("duplicates", 0)
                        stats["errors"] += page_stats.get("errors", 0)
                    except Exception as e:
                        logger.error(f"Unhandled exception in thread: {e}")
                        stats["errors"] += 1

        except Exception as e:
            logger.error(f"Critical error during monitor execution for {base_url}: {e}")
            stats["errors"] += 1

        stats["time"] = round(time.time() - start_time, 2)
        logger.info(f"Monitoring completed for {article_name}. Stats: {stats}")
        return stats

    def _process_monitored_page(self, page_link: Dict[str, Any], article_name: str) -> Dict[str, int]:
        """
        Downloads a specific monitored page, extracts notifications, checks duplicates,
        and triggers downstream AI & Telegram workflows.
        
        Args:
            page_link (Dict[str, Any]): Dictionary containing 'url'.
            article_name (str): Name of the parent article/entity.
            
        Returns:
            Dict[str, int]: Page-level statistics.
        """
        page_stats = {"notifications": 0, "new": 0, "duplicates": 0, "errors": 0}
        page_url = page_link.get("url", "")
        
        if not page_url:
            page_stats["errors"] += 1
            return page_stats

        logger.info(f"Monitoring page: {page_url}")

        # 5. Download page (with Retries)
        content, status, content_type = None, 0, ""
        for attempt in range(1, self.max_retries + 1):
            try:
                # Assuming crawler.fetch returns (content, status, content_type, response_time)
                fetch_result = self.crawler.fetch(page_url)
                if len(fetch_result) >= 3:
                    content, status, content_type = fetch_result[:3]
                
                if status == 200 and content:
                    break
                logger.warning(f"Attempt {attempt} failed for page {page_url} (Status: {status})")
            except Exception as e:
                logger.warning(f"Attempt {attempt} crawler exception for page {page_url}: {e}")
            time.sleep(attempt)

        if status != 200 or not content:
            logger.error(f"Failed to fetch monitored page {page_url} after {self.max_retries} retries.")
            page_stats["errors"] += 1
            return page_stats

        # 6. Extract notifications
        try:
            notifications = self.parser.extract_links(page_url, content)
            page_stats["notifications"] = len(notifications)
        except Exception as e:
            logger.error(f"Parser error on page {page_url}: {e}")
            page_stats["errors"] += 1
            return page_stats

        for notif in notifications:
            try:
                notif_url = notif.get("url")
                title = notif.get("title", "Unknown Title")
                published_date = notif.get("published_date", "")

                if not notif_url:
                    continue

                # 7. Skip duplicates
                if self.db.notification_exists(notif_url):
                    logger.debug(f"Duplicate notification skipped: {notif_url}")
                    page_stats["duplicates"] += 1
                    continue

                logger.info(f"New notification detected: {title} | {notif_url}")

                # 8. Download PDF or HTML
                sub_fetch = self.crawler.fetch(notif_url)
                if not sub_fetch or len(sub_fetch) < 3:
                    page_stats["errors"] += 1
                    continue
                    
                sub_content, sub_status, sub_type = sub_fetch[:3]
                
                if sub_status != 200 or not sub_content:
                    logger.error(f"Failed to download notification content: {notif_url}")
                    page_stats["errors"] += 1
                    continue

                # 9. Extract text
                text_content = ""
                if "pdf" in str(sub_type).lower():
                    logger.info(f"Extracting text from PDF: {notif_url}")
                    text_content = extract_text_from_pdf(sub_content)
                else:
                    logger.info(f"Extracting text from HTML: {notif_url}")
                    soup = BeautifulSoup(sub_content, "html.parser")
                    text_content = soup.get_text(separator=" ", strip=True)

                if not text_content.strip():
                    logger.warning(f"Empty text content extracted for {notif_url}")
                    page_stats["errors"] += 1
                    continue

                # 10. AI Summary
                ai_result = self.ai.analyze_notification(text_content, title)
                summary = ai_result.get("summary", "")
                category = ai_result.get("category", "Unknown")
                ai_status = ai_result.get("status", "Pending")
                confidence = float(ai_result.get("confidence", 0.0))

                # 11. Telegram Notifier
                self.notifier.send_alert(article_name, page_url, notif, ai_result)

                # 12. Save NotificationDatabase
                saved = self.db.save_notification(
                    article=article_name,
                    title=title,
                    url=notif_url,
                    published_date=published_date,
                    summary=summary,
                    category=category,
                    status=ai_status,
                    confidence=confidence
                )

                if saved:
                    page_stats["new"] += 1
                else:
                    page_stats["errors"] += 1

            except Exception as e:
                logger.error(f"Error processing individual notification {notif.get('url')}: {e}")
                page_stats["errors"] += 1

        return page_stats