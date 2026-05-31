import logging
import os
import re

import requests
from pypdf import PdfReader

from .utils import sanitize_filename, polite_sleep

logger = logging.getLogger("trend-letter")

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
TIMEOUT = 60
MAX_SIZE = 50 * 1024 * 1024  # 50 MB

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
}


def download_pdf(pdf_url: str, source_name: str = "") -> str | None:
    """PDF 다운로드 후 로컬 경로 반환. 실패 시 None."""
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    try:
        polite_sleep(1.0)
        resp = requests.get(pdf_url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        resp.raise_for_status()

        cl = resp.headers.get("Content-Length")
        if cl and int(cl) > MAX_SIZE:
            logger.warning(f"PDF 크기 초과 ({int(cl) / 1024 / 1024:.1f}MB): {pdf_url}")
            return None

        # 파일명
        filename = _extract_filename(resp, pdf_url)
        if source_name:
            filename = f"{sanitize_filename(source_name)}_{filename}"
        filepath = os.path.join(DOWNLOADS_DIR, filename)

        total = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(8192):
                total += len(chunk)
                if total > MAX_SIZE:
                    logger.warning(f"PDF 다운로드 중 크기 초과: {pdf_url}")
                    break
                f.write(chunk)
            else:
                logger.info(f"PDF 다운로드 완료: {filename} ({total / 1024:.0f}KB)")
                return filepath

        # 크기 초과로 break 된 경우
        os.remove(filepath)
        return None

    except Exception as e:
        logger.error(f"PDF 다운로드 실패 ({pdf_url}): {e}")
        return None


def extract_text(filepath: str) -> str:
    """PDF에서 텍스트 추출."""
    try:
        reader = PdfReader(filepath)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        result = "\n\n".join(pages)
        if not result.strip():
            logger.warning(f"PDF 텍스트 없음 (이미지 PDF 가능): {filepath}")
        return result
    except Exception as e:
        logger.error(f"PDF 텍스트 추출 실패 ({filepath}): {e}")
        return ""


def _extract_filename(resp: requests.Response, url: str) -> str:
    cd = resp.headers.get("Content-Disposition", "")
    match = re.search(r'filename[*]?=["\']?([^"\';\n]+)', cd)
    if match:
        name = match.group(1).strip()
    else:
        name = url.split("/")[-1].split("?")[0]
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return sanitize_filename(name)
