"""
core.matcher
NotifyAI V4.2 Professional

Keyword Matching Engine
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


# ==========================================================
# Data Model
# ==========================================================

@dataclass(slots=True)
class MatchResult:
    """
    Result of a keyword match.
    """

    matched: bool

    score: float

    matched_keywords: List[str]

    confidence: str


# ==========================================================
# Matcher
# ==========================================================

class Matcher:

    """
    Professional Keyword Matcher
    """

    def __init__(self):

        self.threshold = 0.60

    # ------------------------------------------------------

    @staticmethod
    def normalize(text: str) -> str:

        text = text.lower()

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ------------------------------------------------------

    def tokenize(self, text: str) -> List[str]:

        return re.findall(
            r"[a-zA-Z0-9]+",
            self.normalize(text),
        )

    # ------------------------------------------------------

    def keyword_match(

        self,

        text: str,

        keywords: List[str],

    ) -> MatchResult:

        text = self.normalize(text)

        matched = []

        for keyword in keywords:

            keyword = keyword.strip().lower()

            if keyword in text:

                matched.append(keyword)

        score = len(matched) / max(len(keywords), 1)

        confidence = self.score_to_level(score)

        return MatchResult(

            matched=score > 0,

            score=score,

            matched_keywords=matched,

            confidence=confidence,

        )

    # ------------------------------------------------------

    @staticmethod
    def score_to_level(score: float) -> str:

        if score >= 0.90:
            return "VERY HIGH"

        if score >= 0.75:
            return "HIGH"

        if score >= 0.50:
            return "MEDIUM"

        if score >= 0.25:
            return "LOW"

        return "NONE"

    # ------------------------------------------------------

    def exact_match(

        self,

        title: str,

        keywords: List[str],

    ) -> bool:

        title = self.normalize(title)

        return any(

            k.lower() == title

            for k in keywords

        )

    # ------------------------------------------------------

    def partial_match(

        self,

        title: str,

        keywords: List[str],

    ) -> bool:

        title = self.normalize(title)

        return any(

            k.lower() in title

            for k in keywords

        )
          # ------------------------------------------------------
    # Similarity Matching
    # ------------------------------------------------------

    def similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """
        Calculate similarity ratio between two strings.
        """

        text1 = self.normalize(text1)
        text2 = self.normalize(text2)

        return round(
            SequenceMatcher(
                None,
                text1,
                text2,
            ).ratio(),
            4,
        )

    # ------------------------------------------------------

    def is_duplicate(
        self,
        title: str,
        previous_titles: List[str],
        threshold: float = 0.90,
    ) -> bool:
        """
        Check duplicate notifications.
        """

        for previous in previous_titles:

            if (
                self.similarity(
                    title,
                    previous,
                )
                >= threshold
            ):
                return True

        return False

    # ------------------------------------------------------

    def best_match(
        self,
        title: str,
        keywords: List[str],
    ) -> Dict:
        """
        Find the best matching keyword.
        """

        title = self.normalize(title)

        best_keyword = ""

        best_score = 0.0

        for keyword in keywords:

            score = self.similarity(
                title,
                keyword,
            )

            if score > best_score:

                best_score = score

                best_keyword = keyword

        return {
            "keyword": best_keyword,
            "score": round(best_score, 4),
            "confidence": self.score_to_level(best_score),
        }

    # ------------------------------------------------------
    # Match Counter
    # ------------------------------------------------------

    def count_matches(
        self,
        text: str,
        keywords: List[str],
    ) -> int:
        """
        Count keyword matches.
        """

        text = self.normalize(text)

        count = 0

        for keyword in keywords:

            if keyword.lower() in text:

                count += 1

        return count

    # ------------------------------------------------------

    def extract_matches(
        self,
        text: str,
        keywords: List[str],
    ) -> Set[str]:
        """
        Return matched keywords.
        """

        text = self.normalize(text)

        found = set()

        for keyword in keywords:

            if keyword.lower() in text:

                found.add(keyword)

        return found

    # ------------------------------------------------------
    # Priority
    # ------------------------------------------------------

    def priority(
        self,
        score: float,
    ) -> str:
        """
        Convert score to priority.
        """

        if score >= 0.95:
            return "CRITICAL"

        if score >= 0.85:
            return "VERY HIGH"

        if score >= 0.70:
            return "HIGH"

        if score >= 0.50:
            return "MEDIUM"

        if score >= 0.30:
            return "LOW"

        return "IGNORE"

    # ------------------------------------------------------

    def match_summary(
        self,
        text: str,
        keywords: List[str],
    ) -> Dict:
        """
        Generate complete matching summary.
        """

        result = self.keyword_match(
            text,
            keywords,
        )

        best = self.best_match(
            text,
            keywords,
        )

        return {
            "matched": result.matched,
            "score": result.score,
            "confidence": result.confidence,
            "matched_keywords": result.matched_keywords,
            "best_keyword": best["keyword"],
            "priority": self.priority(result.score),
        }
          # ------------------------------------------------------
    # Fuzzy Matching
    # ------------------------------------------------------

    def fuzzy_match(
        self,
        text: str,
        keywords: List[str],
        threshold: float = 0.70,
    ) -> MatchResult:
        """
        Fuzzy keyword matching.
        """

        text = self.normalize(text)

        matched = []
        scores = []

        for keyword in keywords:

            score = self.similarity(text, keyword)

            if score >= threshold:
                matched.append(keyword)
                scores.append(score)

        avg_score = (
            sum(scores) / len(scores)
            if scores
            else 0.0
        )

        return MatchResult(
            matched=len(matched) > 0,
            score=round(avg_score, 4),
            matched_keywords=matched,
            confidence=self.score_to_level(avg_score),
        )

    # ------------------------------------------------------
    # PDF Matching
    # ------------------------------------------------------

    def pdf_match(
        self,
        pdf_text: str,
        keywords: List[str],
    ) -> Dict:
        """
        Match keywords against PDF text.
        """

        result = self.keyword_match(
            pdf_text,
            keywords,
        )

        return {
            "source": "PDF",
            "matched": result.matched,
            "score": result.score,
            "keywords": result.matched_keywords,
            "confidence": result.confidence,
        }

    # ------------------------------------------------------
    # HTML Matching
    # ------------------------------------------------------

    def html_match(
        self,
        html_text: str,
        keywords: List[str],
    ) -> Dict:
        """
        Match keywords against HTML content.
        """

        result = self.keyword_match(
            html_text,
            keywords,
        )

        return {
            "source": "HTML",
            "matched": result.matched,
            "score": result.score,
            "keywords": result.matched_keywords,
            "confidence": result.confidence,
        }

    # ------------------------------------------------------
    # AI Score
    # ------------------------------------------------------

    def ai_score(
        self,
        title: str,
        content: str,
        keywords: List[str],
    ) -> float:
        """
        Generate an overall relevance score.
        """

        title_result = self.keyword_match(
            title,
            keywords,
        )

        content_result = self.keyword_match(
            content,
            keywords,
        )

        score = (
            title_result.score * 0.6
            + content_result.score * 0.4
        )

        return round(score, 4)

    # ------------------------------------------------------
    # Notification Ranking
    # ------------------------------------------------------

    def rank_notification(
        self,
        title: str,
        content: str,
        keywords: List[str],
    ) -> Dict:
        """
        Rank a notification.
        """

        score = self.ai_score(
            title,
            content,
            keywords,
        )

        return {
            "title": title,
            "score": score,
            "priority": self.priority(score),
            "confidence": self.score_to_level(score),
        }

    # ------------------------------------------------------
    # Batch Matching
    # ------------------------------------------------------

    def batch_match(
        self,
        texts: List[str],
        keywords: List[str],
    ) -> List[Dict]:
        """
        Match multiple texts.
        """

        results = []

        for text in texts:

            results.append(
                self.match_summary(
                    text,
                    keywords,
                )
            )

        return results

    # ------------------------------------------------------
    # Logging
    # ------------------------------------------------------

    def log_match(
        self,
        result: MatchResult,
    ) -> None:
        """
        Log matching result.
        """

        logger.info(
            "Matched=%s Score=%.2f Confidence=%s Keywords=%s",
            result.matched,
            result.score,
            result.confidence,
            ", ".join(result.matched_keywords),
        )
          # ------------------------------------------------------
    # Duplicate Clustering
    # ------------------------------------------------------

    def cluster_duplicates(
        self,
        titles: List[str],
        threshold: float = 0.90,
    ) -> List[List[str]]:
        """
        Group similar notification titles together.
        """

        clusters: List[List[str]] = []

        used = set()

        for i, title in enumerate(titles):

            if i in used:
                continue

            group = [title]

            used.add(i)

            for j, other in enumerate(titles):

                if j in used:
                    continue

                if self.similarity(title, other) >= threshold:

                    group.append(other)

                    used.add(j)

            clusters.append(group)

        return clusters

    # ------------------------------------------------------
    # Filter Notifications
    # ------------------------------------------------------

    def filter_notifications(
        self,
        notifications: List[Dict],
        keywords: List[str],
    ) -> List[Dict]:
        """
        Return only relevant notifications.
        """

        results = []

        for item in notifications:

            title = item.get("title", "")

            content = item.get("content", "")

            score = self.ai_score(
                title,
                content,
                keywords,
            )

            if score >= self.threshold:

                item["score"] = score

                item["priority"] = self.priority(score)

                results.append(item)

        results.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return results

    # ------------------------------------------------------
    # Keyword Frequency
    # ------------------------------------------------------

    def keyword_frequency(
        self,
        text: str,
        keywords: List[str],
    ) -> Dict[str, int]:
        """
        Count keyword frequency.
        """

        text = self.normalize(text)

        frequency = {}

        for keyword in keywords:

            frequency[keyword] = text.count(
                keyword.lower()
            )

        return frequency

    # ------------------------------------------------------
    # Extract Important Keywords
    # ------------------------------------------------------

    def extract_keywords(
        self,
        text: str,
        minimum_length: int = 4,
    ) -> List[str]:
        """
        Extract unique keywords.
        """

        words = self.tokenize(text)

        words = [

            word

            for word in words

            if len(word) >= minimum_length

        ]

        return sorted(set(words))

    # ------------------------------------------------------
    # Statistics
    # ------------------------------------------------------

    def statistics(
        self,
        texts: List[str],
        keywords: List[str],
    ) -> Dict:
        """
        Matching statistics.
        """

        matched = 0

        ignored = 0

        scores = []

        for text in texts:

            result = self.keyword_match(
                text,
                keywords,
            )

            scores.append(result.score)

            if result.matched:

                matched += 1

            else:

                ignored += 1

        average = (

            sum(scores) / len(scores)

            if scores

            else 0

        )

        return {

            "total": len(texts),

            "matched": matched,

            "ignored": ignored,

            "average_score": round(
                average,
                4,
            ),

        }


# ==========================================================
# Module Export
# ==========================================================

__all__ = [

    "Matcher",

    "MatchResult",

]

logger.info(
    "Matcher Engine Loaded Successfully."
)
