import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict

class Parser:
    """Parses HTML documents to discover potential notifications."""
    
    TARGET_KEYWORDS = [
        "notice", "announcement", "circular", "update", "notification",
        "result", "counselling", "admission", "job", "recruitment", 
        "merit list", "schedule", "allotment", "admit card"
    ]

    def extract_links(self, base_url: str, html_bytes: bytes) -> List[Dict[str, str]]:
        """Extracts and filters links relevant to notifications."""
        soup = BeautifulSoup(html_bytes, "html.parser")
        links = []
        
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"]
            
            if not text:
                text = a_tag.get("title", "")
                
            text_lower = text.lower()
            
            # Check if link text contains any target keywords
            if any(kw in text_lower for kw in self.TARGET_KEYWORDS):
                full_url = urljoin(base_url, href)
                content_hash = hashlib.md5(f"{full_url}{text}".encode()).hexdigest()
                
                links.append({
                    "title": text,
                    "url": full_url,
                    "hash": content_hash
                })
                
        return links