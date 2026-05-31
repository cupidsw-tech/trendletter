"""크롤링 → 요약 → DB 저장 → 발송 오케스트레이터."""
import hashlib
import logging
import os
import sys
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

# 엔진 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.models import Article, Source, User, DeliveryLog
from src.crawler import crawl_site, fetch_detail, Article as CrawlArticle
from src.summarizer import summarize
from src.pdf_handler import download_pdf, extract_text
from src.utils import truncate, make_hash
from services.delivery_service import deliver_to_user

logger = logging.getLogger("trend-letter")

# 수집 정책 (v1 봇과 동일)
MAX_PER_SITE = 3            # 사이트당 최대 3건 (최근 글 위주)
MAX_UNDATED_PER_SITE = 1   # 날짜 불명은 사이트당 1건

# 영업/안내성 항목 제외 키워드 (제목·파일명 대상)
NOISE_KEYWORDS = (
    "매체소개서", "매체 소개서", "매체소개", "소개서", "미디어킷", "media kit", "mediakit",
    "광고문의", "제휴문의", "단가표", "광고상품", "회사소개", "서비스소개",
)


def _is_noise(*texts) -> bool:
    from urllib.parse import unquote
    parts = []
    for t in texts:
        t = t or ""
        parts.append(t)
        parts.append(unquote(t))  # 퍼센트 인코딩된 한글 파일명/URL도 검사
    hay = " ".join(parts).lower()
    return any(k.lower() in hay for k in NOISE_KEYWORDS)


def _parse_date(date_str):
    """RSS/문자 날짜 → YYYY-MM-DD. 실패 시 None."""
    import re
    if not date_str:
        return None
    s = date_str.strip()
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:31].strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return None


def _is_recent(date_str):
    """최근 1일이면 True / 지난 글 False / 날짜불명 None."""
    d = _parse_date(date_str)
    if not d:
        return None
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return d >= yesterday


def _cuid() -> str:
    """간단한 고유 ID 생성."""
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:25]


def run_batch_crawl(db: Session, user_id: str, sources: list[dict]) -> dict:
    """사용자의 모든 소스를 크롤링 → 요약 → 저장 → 발송."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    stats = {"new_articles": 0, "new_pdfs": 0, "failed": 0}

    for src_info in sources:
        try:
            new_articles = _crawl_single_source(db, src_info)
            stats["new_articles"] += len(new_articles)

            # 발송
            if new_articles:
                deliver_to_user(db, user, new_articles, src_info.get("name", ""))

        except Exception as e:
            logger.error(f"소스 크롤링 실패 ({src_info.get('name')}): {e}")
            stats["failed"] += 1

    return stats


def _crawl_single_source(db: Session, src_info: dict) -> list[Article]:
    """단일 소스 크롤링 → 요약 → DB 저장. 새로 저장된 Article 리스트 반환."""
    source_id = src_info["source_id"]
    site = {
        "url": src_info["url"],
        "name": src_info.get("name", ""),
        "category": src_info.get("category", "기타"),
    }

    # 크롤링
    crawl_articles = crawl_site(site)
    if not crawl_articles:
        _update_last_crawled(db, source_id)
        return []

    new_db_articles = []
    undated = 0

    for article in crawl_articles:
        if len(new_db_articles) >= MAX_PER_SITE:
            break

        content_hash = make_hash(article.url or article.title)

        # DB에서 중복 체크 (이미 보낸 글 재수집 방지)
        existing = db.query(Article).filter(
            Article.source_id == source_id,
            Article.content_hash == content_hash,
        ).first()
        if existing:
            continue

        # 영업/안내성(매체소개서 등) 제목 제외
        if _is_noise(article.title):
            logger.info(f"  제외(영업성): {article.title}")
            continue

        # 최근 1일 필터
        recent = _is_recent(article.date)
        if recent is False:
            continue
        if recent is None:
            if undated >= MAX_UNDATED_PER_SITE:
                continue
            undated += 1

        # 상세 페이지
        try:
            article = fetch_detail(article)
        except Exception as e:
            logger.warning(f"  상세 페이지 실패: {e}")

        # PDF 처리 (영업성 파일명은 첨부에서 제외)
        pdf_urls_result = []
        for pdf_url in article.pdf_urls:
            try:
                if _is_noise(pdf_url):
                    logger.info(f"  첨부 제외(영업성): {pdf_url}")
                    continue
                if pdf_url.startswith("local:"):
                    local_path = pdf_url[6:]
                    if os.path.exists(local_path):
                        pdf_urls_result.append(pdf_url)
                    continue
                path = download_pdf(pdf_url, article.source_name)
                if path:
                    pdf_urls_result.append(pdf_url)
            except Exception as e:
                logger.warning(f"  PDF 다운로드 실패: {e}")

        # PDF 텍스트 추출
        pdf_text = ""
        for pf_url in pdf_urls_result:
            if pf_url.startswith("local:"):
                path = pf_url[6:]
            else:
                path = download_pdf(pf_url, article.source_name)
            if path:
                try:
                    pdf_text += extract_text(path) + "\n"
                except Exception:
                    pass

        # AI 요약
        text_for_summary = article.body or ""
        if pdf_text.strip():
            text_for_summary += "\n\n[PDF 내용]\n" + pdf_text

        has_pdf = bool(pdf_text.strip())
        summary = None
        if text_for_summary.strip():
            try:
                summary = summarize(
                    text_for_summary,
                    title=article.title,
                    category=article.category,
                    is_pdf=has_pdf,
                )
            except Exception as e:
                logger.warning(f"  AI 요약 실패: {e}")

        if not summary:
            summary = truncate(article.body, 500) if article.body else "(본문 수집 불가)"

        # DB 저장
        db_article = Article(
            id=_cuid(),
            source_id=source_id,
            content_hash=content_hash,
            title=article.title,
            url=article.url,
            date=article.date,
            body=article.body,
            summary=summary,
            pdf_urls=pdf_urls_result,
            crawled_at=datetime.utcnow(),
        )

        try:
            db.add(db_article)
            db.commit()
            new_db_articles.append(db_article)
        except Exception:
            db.rollback()
            continue

    _update_last_crawled(db, source_id)
    return new_db_articles


def _update_last_crawled(db: Session, source_id: str):
    db.query(Source).filter(Source.id == source_id).update(
        {"last_crawled_at": datetime.utcnow()}
    )
    db.commit()
