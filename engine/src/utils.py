import hashlib
import logging
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"bot_{datetime.now():%Y%m%d}.log")

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Windows 콘솔 한글 깨짐 방지
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(formatter)

    root = logging.getLogger("trend-letter")
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    return root


def make_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:150] if len(name) > 150 else name


def resolve_url(base: str, relative: str) -> str:
    return urljoin(base, relative)


def get_domain(url: str) -> str:
    return urlparse(url).netloc


def polite_sleep(seconds: float = 2.0):
    time.sleep(seconds)


def truncate(text: str, max_len: int = 3000) -> str:
    return text if len(text) <= max_len else text[:max_len] + "\n...(이하 생략)"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(date_str: str) -> str | None:
    """다양한 날짜 형식을 YYYY-MM-DD로 통일. 실패 시 None."""
    if not date_str:
        return None
    date_str = date_str.strip()

    # 숫자만 추출해서 시도
    digits = re.sub(r"[^\d]", "", date_str)

    patterns = [
        # 2026-05-10, 2026.05.10, 2026/05/10
        (r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", "%Y-%m-%d"),
        # 05.10, 05-10 (올해로 추정)
        (r"^(\d{1,2})[.\-/](\d{1,2})$", None),
    ]

    for pattern, fmt in patterns:
        m = re.search(pattern, date_str)
        if m:
            groups = m.groups()
            if len(groups) == 3:
                try:
                    y, mo, d = int(groups[0]), int(groups[1]), int(groups[2])
                    return f"{y:04d}-{mo:02d}-{d:02d}"
                except ValueError:
                    continue
            elif len(groups) == 2:
                try:
                    mo, d = int(groups[0]), int(groups[1])
                    y = datetime.now().year
                    return f"{y:04d}-{mo:02d}-{d:02d}"
                except ValueError:
                    continue

    # 8자리 숫자 (20260510)
    if len(digits) >= 8:
        try:
            dt = datetime.strptime(digits[:8], "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # RSS 날짜 형식 (Mon, 10 May 2026 ...)
    rss_patterns = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in rss_patterns:
        try:
            dt = datetime.strptime(date_str[:30].strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None
