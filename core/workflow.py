"""
NotifyAI V3 - Workflow Module
Provides the WorkflowEngine class to orchestrate the top-level execution
of the continuous monitoring system across all active articles.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class WorkflowEngine:
    """
    Orchestrates the entire NotifyAI V3 workflow by syncing configurations,
    loading target articles, and concurrently executing the MonitorEngine.
    """

    def __init__(self, database: Any, monitor_engine: Any, max_workers: int = 5) -> None:
        """
        Initializes the WorkflowEngine.

        Args:
            database (Any): An instance of the main Database class for syncing and retrieving articles.
            monitor_engine (Any): An instance of MonitorEngine to execute the site-specific workflow.
            max_workers (int): Maximum number of concurrent threads. Defaults to 5.
        """
        self.db = database
        self.monitor_engine = monitor_engine
        self.max_workers = max_workers

    def run(self) -> Dict[str, Any]:
        """
        Executes the main workflow:
        1. Syncs Excel to the Database.
        2. Retrieves active articles.
        3. Runs monitoring concurrently for all articles.
        4. Collects and returns execution statistics.

        Returns:
            Dict[str, Any]: Aggregated workflow execution statistics.
        """
        start_time = time.time()
        
        stats = {
            "articles": 0,
            "success": 0,
            "failed": 0,
            "notifications": 0,
            "duplicates": 0,
            "runtime": 0.0
        }

        logger.info("Starting NotifyAI V3 Workflow execution.")

        try:
            # 1. Sync Excel
            logger.info("Syncing Excel data to database...")
            self.db.sync_excel_to_db()

            # 2. Load Active Articles
            logger.info("Retrieving active articles...")
            articles: List[Dict[str, Any]] = self.db.get_active_articles()
            stats["articles"] = len(articles)

        except Exception as e:
            logger.error(f"Critical failure during initialization phase: {e}")
            stats["runtime"] = round(time.time() - start_time, 2)
            return stats

        if not articles:
            logger.warning("No active articles found to process.")
            stats["runtime"] = round(time.time() - start_time, 2)
            return stats

        logger.info(f"Loaded {stats['articles']} articles. Commencing concurrent monitoring.")

        # 3. Use ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 4. For every article call MonitorEngine.monitor(article)
            futures = {
                executor.submit(self.monitor_engine.monitor, article): article 
                for article in articles
            }

            for i, future in enumerate(as_completed(futures), 1):
                article = futures[future]
                article_name = article.get("article_name", "Unknown Article")
                
                try:
                    result = future.result()
                    
                    # 5. Collect statistics
                    stats["success"] += 1
                    stats["notifications"] += result.get("notifications", 0)
                    stats["duplicates"] += result.get("duplicates", 0)
                    
                    logger.info(f"Progress: [{i}/{stats['articles']}] Successfully processed '{article_name}'.")
                    
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Progress: [{i}/{stats['articles']}] Failed to process '{article_name}': {e}")

        # Finalize runtime
        stats["runtime"] = round(time.time() - start_time, 2)
        
        logger.info(f"Workflow completed successfully. Final Statistics: {stats}")
        
        # 6. Return statistics
        return stats