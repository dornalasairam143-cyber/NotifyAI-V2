"""
NotifyAI V2 - Website Discovery Module
Provides the WebsiteDiscovery class for extracting, scoring, and filtering 
highly relevant notification links from government and official websites.
"""

import logging
import time
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional

import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class WebsiteDiscovery:
    """
    Handles discovery of notification links from a given base URL.
    Fetches the homepage, extracts all anchor tags, normalizes URLs, 
    and applies a scoring mechanism to filter high-value links.
    """

    def __init__(self) -> None:
        """
        Initializes the WebsiteDiscovery with a requests Session,
        and defines the keywords used for filtering and scoring links.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        self.timeout = 10
        self.max_retries = 3

        # Scoring configuration
        self.high_priority_keywords = [
            "notification", "notice", "admission", "registration", 
            "cap", "counselling", "important", "recruitment", 
            "result", "download", "pdf"
        ]
        self.low_priority_keywords = [
            "gallery", "photo", "contact", "about", "vision", "mission"
        ]
        self.ignored_signatures = [
            "facebook", "instagram", "twitter", "youtube", "mailto:", "javascript:"
        ]

    def discover(self, base_url: str) -> List[Dict[str, Any]]:
        """
        Downloads the homepage, extracts links, scores them, and filters results.

        Args:
            base_url (str): The homepage URL to discover links from.

        Returns:
            List[Dict[str, Any]]: A sorted list of highly scored link dictionaries.
        """
        logger.info(f"Starting discovery on: {base_url}")
        content = self._fetch_with_retry(base_url)
        
        if not content:
            logger.warning(f"Failed to retrieve content for discovery from {base_url}")
            return []

        try:
            soup = BeautifulSoup(content, "html.parser")
            anchors = soup.find_all("a")
            logger.info(f"Extracted {len(anchors)} raw <a> tags from {base_url}")
        except Exception as e:
            logger.error(f"Error parsing HTML for {base_url}: {e}")
            return []

        raw_links = []
        for tag in anchors:
            href = tag.get("href")
            title = tag.get_text(separator=" ", strip=True)
            
            if not href:
                continue
                
            absolute_url = urljoin(base_url, href)
            raw_links.append({"title": title, "url": absolute_url})

        filtered_results = self.filter_links(raw_links)
        logger.info(f"Discovery completed for {base_url}. Found {len(filtered_results)} viable links.")
        
        return filtered_results

    def filter_links(self, links: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Filters and sorts a list of links based on their calculated score.
        Deduplicates links by URL to prevent redundant processing.

        Args:
            links (List[Dict[str, str]]): List of raw link dictionaries containing 'title' and 'url'.

        Returns:
            List[Dict[str, Any]]: Filtered and sorted list of links with score >= 50.
        """
        scored_links = []
        seen_urls = set()

        for link in links:
            url = link.get("url", "")
            title = link.get("title", "")

            if url in seen_urls:
                continue

            # Ignore social media, emails, and javascript links
            url_lower = url.lower()
            if any(ignored in url_lower for ignored in self.ignored_signatures):
                continue

            score = self.score_link(title, url)
            
            if score >= 50:
                scored_links.append({
                    "title": title,
                    "url": url,
                    "score": score
                })
                seen_urls.add(url)

        # Sort by highest score first
        scored_links.sort(key=lambda x: x["score"], reverse=True)
        return scored_links

    def score_link(self, title: str, url: str) -> int:
        """
        Calculates a priority score for a given link based on its title and URL.

        Args:
            title (str): The visible text of the link.
            url (str): The absolute URL of the link.

        Returns:
            int: The computed score (0-100).
        """
        score = 0
        title_lower = title.lower()
        url_lower = url.lower()

        # Add points for high priority keywords
        for keyword in self.high_priority_keywords:
            if keyword in title_lower:
                score += 50
            if keyword in url_lower:
                score += 30

        # Subtract points for low priority keywords
        for keyword in self.low_priority_keywords:
            if keyword in title_lower or keyword in url_lower:
                score -= 60

        # Clamp score between 0 and 100
        return max(0, min(score, 100))

    def _fetch_with_retry(self, url: str) -> Optional[bytes]:
        """
        Internal method to fetch URL content with retries and timeout.

        Args:
            url (str): The URL to fetch.

        Returns:
            Optional[bytes]: The raw response content if successful, None otherwise.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except RequestException as e:
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed for {url}: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 * attempt)  # Exponential backoff
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {url}")
                    return None
        return None