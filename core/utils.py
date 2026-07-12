"""
core/utils.py
NotifyAI V4.2 Professional Utility Module

Provides common helper functions used throughout NotifyAI.

Compatible:
- Python 3.12+
- Windows
- Linux
- GitHub Actions
- Codespaces
"""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
import random
import re
import socket
import tempfile
import threading
import time
import unicodedata
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional
from urllib.parse import (
    urljoin,
    urlparse,
    urlunparse,
    parse_qsl,
    urlencode,
)

logger = logging.getLogger(__name__)

# ==========================================================
# Thread-safe Singleton
# ==========================================================

_singletons: Dict[type, Any] = {}
_singleton_lock = threading.Lock()


def singleton(cls):
    """Thread-safe singleton decorator."""

    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in _singletons:
            with _singleton_lock:
                if cls not in _singletons:
                    _singletons[cls] = cls(*args, **kwargs)
        return _singletons[cls]

    return wrapper


# ==========================================================
# Execution Timer
# ==========================================================


def timer(func):
    """Measure execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()

        result = func(*args, **kwargs)

        elapsed = time.perf_counter() - start

        logger.debug(
            "%s executed in %.3f sec",
            func.__name__,
            elapsed,
        )

        return result

    return wrapper


# ==========================================================
# Retry Decorator
# ==========================================================


def retry(
    attempts: int = 3,
    delay: float = 1,
    backoff: float = 2,
):
    """Retry decorator."""

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            current_delay = delay

            last_exception = None

            for _ in range(attempts):

                try:
                    return func(*args, **kwargs)

                except Exception as exc:

                    last_exception = exc

                    logger.warning(
                        "%s failed (%s). Retrying...",
                        func.__name__,
                        exc,
                    )

                    time.sleep(current_delay)

                    current_delay *= backoff

            raise last_exception

        return wrapper

    return decorator


# ==========================================================
# Hash Functions
# ==========================================================


def sha256(data: str | bytes) -> str:
    """Return SHA256 hash."""

    if isinstance(data, str):
        data = data.encode("utf-8")

    return hashlib.sha256(data).hexdigest()


def md5(data: str | bytes) -> str:
    """Return MD5 hash."""

    if isinstance(data, str):
        data = data.encode("utf-8")

    return hashlib.md5(data).hexdigest()


def file_hash(path: str | Path) -> str:
    """Hash file."""

    h = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


# ==========================================================
# URL Utilities
# ==========================================================


def normalize_url(url: str) -> str:
    """Normalize URL."""

    parsed = urlparse(url.strip())

    scheme = parsed.scheme.lower() or "https"

    netloc = parsed.netloc.lower()

    return urlunparse(
        (
            scheme,
            netloc,
            parsed.path,
            "",
            parsed.query,
            "",
        )
    )


def remove_tracking(url: str) -> str:
    """Remove common tracking parameters."""

    parsed = urlparse(url)

    params = parse_qsl(parsed.query)

    ignore = (
        "utm_",
        "fbclid",
        "gclid",
        "_ga",
    )

    filtered = []

    for key, value in params:

        if key.startswith(ignore):
            continue

        filtered.append((key, value))

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",
            urlencode(filtered),
            "",
        )
    )


def clean_url(url: str) -> str:
    """Normalize and clean URL."""

    return remove_tracking(normalize_url(url))


def valid_url(url: str) -> bool:
    """Basic URL validation."""

    try:

        parsed = urlparse(url)

        return bool(parsed.scheme and parsed.netloc)

    except Exception:

        return False


def join(base: str, path: str) -> str:
    """Join URL."""

    return urljoin(base, path)


def is_pdf(url: str) -> bool:
    """Return True if URL points to PDF."""

    return url.lower().endswith(".pdf")


def extension(path: str | Path) -> str:
    """Return file extension."""

    return Path(path).suffix.lower()


def mime_type(path: str | Path) -> str:
    """Return mime type."""

    mime, _ = mimetypes.guess_type(str(path))

    return mime or "application/octet-stream"
  # ==========================================================
# Text Utilities
# ==========================================================

def normalize_text(text: str) -> str:
    """Normalize text."""

    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\r", " ")

    text = text.replace("\n", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def strip_html(text: str) -> str:
    """Remove HTML tags."""

    if not text:
        return ""

    return re.sub(r"<[^>]+>", " ", text)


def clean_text(text: str) -> str:
    """Clean HTML and normalize."""

    return normalize_text(strip_html(text))


def slugify(text: str) -> str:
    """Create slug."""

    text = normalize_text(text).lower()

    text = re.sub(r"[^a-z0-9]+", "-", text)

    return text.strip("-")


def tokenize(text: str) -> list[str]:
    """Tokenize."""

    return re.findall(r"[A-Za-z0-9]+", normalize_text(text).lower())


def unique_words(text: str) -> list[str]:
    """Return unique words."""

    return sorted(set(tokenize(text)))


def contains_keyword(
    text: str,
    keywords: list[str],
) -> bool:
    """Keyword search."""

    text = normalize_text(text).lower()

    for keyword in keywords:

        if keyword.lower() in text:
            return True

    return False


# ==========================================================
# Date & Time
# ==========================================================

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Current UTC datetime."""

    return datetime.now(timezone.utc)


def utc_timestamp() -> str:
    """UTC ISO timestamp."""

    return utc_now().isoformat()


def today() -> str:
    """Today's date."""

    return utc_now().strftime("%Y-%m-%d")


def now_string() -> str:
    """Current datetime string."""

    return utc_now().strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(value: str):

    formats = [

        "%Y-%m-%d",

        "%d-%m-%Y",

        "%d/%m/%Y",

        "%Y/%m/%d",

        "%Y-%m-%d %H:%M:%S",

    ]

    for fmt in formats:

        try:

            return datetime.strptime(value, fmt)

        except Exception:

            pass

    return None


def elapsed_seconds(start: float) -> float:

    return round(time.perf_counter() - start, 3)


# ==========================================================
# File Utilities
# ==========================================================


def ensure_folder(folder: str | Path) -> Path:
    """Create folder."""

    path = Path(folder)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def read_text(path: str | Path) -> str:
    """Read text."""

    return Path(path).read_text(
        encoding="utf-8",
        errors="ignore",
    )


def write_text(
    path: str | Path,
    text: str,
):
    """Write text."""

    Path(path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(path).write_text(
        text,
        encoding="utf-8",
    )


def read_json(path: str | Path):

    if not Path(path).exists():

        return {}

    return json.loads(read_text(path))


def write_json(
    path: str | Path,
    obj,
):
    """Write JSON."""

    write_text(
        path,
        json.dumps(
            obj,
            indent=4,
            ensure_ascii=False,
        ),
    )


def temporary_file(
    suffix=".tmp",
):
    """Create temp file."""

    fd, name = tempfile.mkstemp(
        suffix=suffix,
    )

    os.close(fd)

    return Path(name)


def file_size(path: str | Path) -> int:
    """File size."""

    return Path(path).stat().st_size


def exists(path: str | Path) -> bool:

    return Path(path).exists()


def delete(path: str | Path):

    p = Path(path)

    if p.exists():

        p.unlink()


def list_files(folder: str | Path):

    return list(Path(folder).glob("*"))
  # ==========================================================
# Network Utilities
# ==========================================================

def internet_available(
    host: str = "8.8.8.8",
    port: int = 53,
    timeout: float = 3.0,
) -> bool:
    """Check internet connectivity."""

    try:
        socket.setdefaulttimeout(timeout)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))

        return True

    except OSError:
        return False


def default_headers() -> dict:
    """Default HTTP headers."""

    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (X11; Linux x86_64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    ]

    return {
        "User-Agent": random.choice(agents),
        "Accept": "*/*",
        "Connection": "keep-alive",
    }


# ==========================================================
# Safe Filename
# ==========================================================


def safe_filename(filename: str) -> str:
    """Return filesystem-safe filename."""

    filename = normalize_text(filename)

    filename = re.sub(
        r'[\\/:*?"<>|]',
        "_",
        filename,
    )

    filename = filename.replace(" ", "_")

    return filename.strip("_")


# ==========================================================
# UUID & Random
# ==========================================================


def uuid4() -> str:
    """Generate UUID4."""

    return str(uuid.uuid4())


def random_string(length: int = 16) -> str:
    """Random alphanumeric string."""

    alphabet = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
    )

    return "".join(
        random.choice(alphabet)
        for _ in range(length)
    )


# ==========================================================
# Environment Variables
# ==========================================================


def getenv(
    key: str,
    default: str = "",
) -> str:
    """Read environment variable."""

    return os.getenv(key, default)


def require_env(key: str) -> str:
    """Read mandatory environment variable."""

    value = os.getenv(key)

    if not value:
        raise RuntimeError(
            f"Environment variable '{key}' not found."
        )

    return value


# ==========================================================
# Dictionary Helpers
# ==========================================================


def dict_get(
    data: dict,
    key,
    default=None,
):
    """Safe dictionary getter."""

    if not isinstance(data, dict):
        return default

    return data.get(key, default)


def nested_get(
    data: dict,
    keys: list,
    default=None,
):
    """Safe nested getter."""

    value = data

    for key in keys:

        if not isinstance(value, dict):

            return default

        value = value.get(key)

        if value is None:

            return default

    return value


# ==========================================================
# Type Conversion
# ==========================================================


def to_bool(value) -> bool:
    """Convert to bool."""

    if isinstance(value, bool):
        return value

    if value is None:
        return False

    return str(value).lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def to_int(
    value,
    default: int = 0,
) -> int:
    """Safe int."""

    try:
        return int(value)

    except Exception:
        return default


def to_float(
    value,
    default: float = 0.0,
) -> float:
    """Safe float."""

    try:
        return float(value)

    except Exception:
        return default


# ==========================================================
# Performance
# ==========================================================


class Stopwatch:
    """Simple stopwatch."""

    def __init__(self):

        self.start = time.perf_counter()

    def reset(self):

        self.start = time.perf_counter()

    @property
    def elapsed(self):

        return round(
            time.perf_counter() - self.start,
            3,
        )


# ==========================================================
# Thread Helpers
# ==========================================================


def run_thread(
    target,
    *args,
    daemon=True,
    **kwargs,
):
    """Run daemon thread."""

    thread = threading.Thread(
        target=target,
        args=args,
        kwargs=kwargs,
        daemon=daemon,
    )

    thread.start()

    return thread


# ==========================================================
# Validation
# ==========================================================


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def valid_email(email: str) -> bool:
    """Validate email."""

    return bool(
        EMAIL_PATTERN.match(email.strip())
    )


def valid_file(path: str | Path) -> bool:
    """Check file."""

    return Path(path).is_file()


def valid_folder(path: str | Path) -> bool:
    """Check folder."""

    return Path(path).is_dir()
  # ==========================================================
# List Utilities
# ==========================================================

def chunk_list(items, size):
    """
    Split a list into chunks.
    """

    if size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    for i in range(0, len(items), size):
        yield items[i:i + size]


def flatten(items):
    """
    Flatten nested lists.
    """

    result = []

    for item in items:

        if isinstance(item, (list, tuple, set)):
            result.extend(flatten(item))
        else:
            result.append(item)

    return result


def unique(items):
    """
    Preserve order while removing duplicates.
    """

    seen = set()

    output = []

    for item in items:

        if item not in seen:

            seen.add(item)

            output.append(item)

    return output


# ==========================================================
# Memory Helpers
# ==========================================================

def object_size(obj):
    """
    Return object size in bytes.
    """

    import sys

    return sys.getsizeof(obj)


def memory_usage():
    """
    Return current process memory usage.
    """

    try:

        import psutil

        process = psutil.Process()

        return process.memory_info().rss

    except Exception:

        return 0


# ==========================================================
# Progress
# ==========================================================

def progress(current, total):

    if total <= 0:
        return "0%"

    percent = (current / total) * 100

    return f"{percent:.1f}%"


# ==========================================================
# Misc Helpers
# ==========================================================

def sleep(seconds):

    time.sleep(seconds)


def current_thread():

    return threading.current_thread().name


def current_pid():

    return os.getpid()


# ==========================================================
# Export
# ==========================================================

__all__ = [

    "singleton",

    "timer",

    "retry",

    "sha256",

    "md5",

    "file_hash",

    "normalize_url",

    "remove_tracking",

    "clean_url",

    "valid_url",

    "join",

    "is_pdf",

    "extension",

    "mime_type",

    "normalize_text",

    "strip_html",

    "clean_text",

    "slugify",

    "tokenize",

    "unique_words",

    "contains_keyword",

    "utc_now",

    "utc_timestamp",

    "today",

    "now_string",

    "parse_datetime",

    "elapsed_seconds",

    "ensure_folder",

    "read_text",

    "write_text",

    "read_json",

    "write_json",

    "temporary_file",

    "file_size",

    "exists",

    "delete",

    "list_files",

    "internet_available",

    "default_headers",

    "safe_filename",

    "uuid4",

    "random_string",

    "getenv",

    "require_env",

    "dict_get",

    "nested_get",

    "to_bool",

    "to_int",

    "to_float",

    "Stopwatch",

    "run_thread",

    "valid_email",

    "valid_file",

    "valid_folder",

    "chunk_list",

    "flatten",

    "unique",

    "object_size",

    "memory_usage",

    "progress",

    "sleep",

    "current_thread",

    "current_pid",
]

logger.info("NotifyAI Utils Module Loaded Successfully.")
