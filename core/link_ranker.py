"""
NotifyAI V3 - Link Ranker Module
Provides the LinkRanker class to evaluate, score, and filter discovered links
using a combination of heuristic discovery scores and AI-driven importance evaluation.
"""

import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class LinkRanker:
    """
    Evaluates and ranks webpage links based on heuristic discovery scores
    and AI-classified importance for government admission notifications.
    """

    def __init__(self, ai_classifier: Any) -> None:
        """
        Initializes the LinkRanker.

        Args:
            ai_classifier (Any): An instance of AIClassifier used to evaluate links.
                                 Expected to have an `analyze(prompt: str) -> str` method.
        """
        self.ai = ai_classifier
        self.max_retries = 2
        self.threshold = 70.0
        self.max_results = 10
        self.max_workers = 5

    def rank_links(self, links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks a list of links concurrently using AI evaluation and discovery scores.

        Args:
            links (List[Dict[str, Any]]): List of dicts containing 'title', 'url', and 'score'.

        Returns:
            List[Dict[str, Any]]: Sorted list of the top ranked links (max 10) with score >= 70.
        """
        if not links:
            logger.warning("No links provided to rank.")
            return []

        logger.info(f"Starting ranking process for {len(links)} links.")
        ranked_links: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_link = {
                executor.submit(self._process_single_link, link): link 
                for link in links
            }

            for future in as_completed(future_to_link):
                try:
                    result = future.result()
                    if result and result.get("final_score", 0) >= self.threshold:
                        ranked_links.append(result)
                except Exception as e:
                    logger.error(f"Unhandled exception during link processing: {e}")

        # Sort descending by final_score
        ranked_links.sort(key=lambda x: x["final_score"], reverse=True)

        # Truncate to maximum allowed results
        final_results = ranked_links[:self.max_results]
        logger.info(f"Ranking complete. Yielded {len(final_results)} highly ranked links.")
        
        return final_results

    def _process_single_link(self, link: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluates a single link using the AI classifier, handles retries, and computes the final score.

        Args:
            link (Dict[str, Any]): The link data dictionary.

        Returns:
            Optional[Dict[str, Any]]: The processed link data with final scores, or None if failed.
        """
        title = link.get("title", "")
        url = link.get("url", "")
        discovery_score = float(link.get("score", 0.0))

        if not url:
            return None

        prompt = (
            "Analyze the following webpage link.\n"
            f"Title: {title}\n"
            f"URL: {url}\n\n"
            "Question: Should this page be monitored continuously for government admission notifications?\n\n"
            "Return strictly valid JSON with the following schema:\n"
            "{\n"
            '  "importance": <int 0-100>,\n'
            '  "reason": "<brief reason>",\n'
            '  "category": "<e.g., Admission, Recruitment, General>"\n'
            "}\n"
            "Do not include any markdown formatting, backticks, or additional text outside the JSON object."
        )

        # Retry logic: 1 initial attempt + 2 retries = 3 attempts total
        for attempt in range(self.max_retries + 1):
            try:
                # Assumes the ai_classifier exposes an `analyze` method.
                # Adjust method name based on actual AIClassifier implementation.
                response_text = self.ai.analyze(prompt)
                
                # Sanitize response to ensure valid JSON parsing
                sanitized_text = response_text.strip()
                if sanitized_text.startswith("```json"):
                    sanitized_text = sanitized_text[7:-3].strip()
                elif sanitized_text.startswith("```"):
                    sanitized_text = sanitized_text[3:-3].strip()

                parsed_response = json.loads(sanitized_text)
                
                ai_importance = float(parsed_response.get("importance", 0.0))
                category = str(parsed_response.get("category", "Unknown"))
                reason = str(parsed_response.get("reason", ""))
                
                # Compute Final Score based on given formula
                final_score = (discovery_score * 0.4) + (ai_importance * 0.6)
                
                logger.debug(f"Successfully processed link: {url} | Final Score: {final_score:.2f}")
                
                return {
                    "title": title,
                    "url": url,
                    "final_score": round(final_score, 2),
                    "importance": round(ai_importance, 2),
                    "category": category,
                    "reason": reason
                }

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed for {url} on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.warning(f"AI evaluation failed for {url} on attempt {attempt + 1}: {e}")

            if attempt < self.max_retries:
                time.sleep(1.5 ** attempt)  # Exponential backoff for retries

        logger.error(f"Failed to process link after {self.max_retries + 1} attempts: {url}")
        return None