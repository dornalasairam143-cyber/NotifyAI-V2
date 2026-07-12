import io
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text content from raw PDF bytes."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        # Extract from first 3 pages to save processing time on massive documents
        for page in reader.pages[:3]:
            text_parts.append(page.extract_text() or "")
        return " ".join(text_parts).strip()
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return ""