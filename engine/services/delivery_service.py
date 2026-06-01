"""발송 서비스: 모든 사이트를 하나(필요 시 분할)의 메시지로 취합 발송."""
import html
import logging
import uuid
from datetime import datetime
from urllib.parse import unquote

from sqlalchemy.orm import Session

from core.models import User, Article, DeliveryLog
from src.telegram_sender import send_message as tg_send

logger = logging.getLogger("trend-letter")

SUMMARY_LEN = 220
CHUNK_LIMIT = 3800

NOISE_KEYWORDS = (
    "매체소개서", "매체 소개서", "매체소개", "소개서", "미디어킷", "media kit", "mediakit",
    "광고문의", "제휴문의", "단가표", "광고상품", "회사소개", "서비스소개",
)


def _cuid() -> str:
    return str(uuid.uuid4()).replace("-", "")[:25]


def _is_noise(*texts) -> bool:
    parts = []
    for t in texts:
        t = t or ""
        parts.append(t)
        parts.append(unquote(t))
    hay = " ".join(parts).lower()
    return any(k.lower() in hay for k in NOISE_KEYWORDS)


def _has_pdf(article: Article) -> bool:
    for pu in (article.pdf_urls or []):
        if pu and not _is_noise(pu):
            return True
    return False


def _trunc(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "…"


def _log(db: Session, user_id: str, article_id: str, channel: str, status: str):
    db.add(DeliveryLog(
        id=_cuid(), user_id=user_id, article_id=article_id,
        channel=channel, status=status,
        sent_at=datetime.utcnow() if status == "sent" else None,
    ))
    db.commit()


def _block_html(site_name: str, articles: list) -> str:
    e = html.escape
    cat = e((articles[0].source.category if articles and articles[0].source else "") or "기타")
    lines = [f"\n🏷️ <b>[{cat}] {e(site_name)}</b>"]
    for i, art in enumerate(articles, 1):
        title = e(art.title or "(제목 없음)")
        url = e(art.url or "")
        summary = e(_trunc(art.summary or "", SUMMARY_LEN))
        line = f'{i}. <a href="{url}">{title}</a>\n{summary}'
        if _has_pdf(art):
            line += "\n📎 본문에 PDF 자료 있음 (원문에서 확인)"
        lines.append(line)
    return "\n".join(lines)


def deliver_combined(db: Session, user: User, blocks: list):
    """blocks: [(site_name, [Article,...]), ...] → 웹 로그 + 텔레그램 통합 발송."""
    today = datetime.now().strftime("%Y.%m.%d")

    # 웹 (DB엔 이미 저장됨 — 로그만)
    if user.deliver_web:
        for _, articles in blocks:
            for art in articles:
                _log(db, user.id, art.id, "web", "sent")

    # 텔레그램: 모든 사이트를 하나(4096 초과 시 분할)의 메시지로
    if user.deliver_telegram and user.telegram_chat_id:
        header = f"📰 <b>트렌드레터</b> · {today}\n━━━━━━━━━━━━━━━━━━"
        chunks, cur = [], header
        for site_name, articles in blocks:
            bs = _block_html(site_name, articles)
            if len(cur) + len(bs) + 2 > CHUNK_LIMIT:
                chunks.append(cur)
                cur = bs.lstrip("\n")
            else:
                cur += "\n" + bs
        if cur.strip():
            chunks.append(cur)

        total = len(chunks)
        all_ok = True
        for idx, c in enumerate(chunks, 1):
            if total > 1:
                c += f"\n\n— ({idx}/{total}) —"
            if not tg_send(c, user.telegram_chat_id, parse_mode="HTML"):
                all_ok = False

        for _, articles in blocks:
            for art in articles:
                _log(db, user.id, art.id, "telegram", "sent" if all_ok else "failed")


# 하위호환
def deliver_to_user(db: Session, user: User, articles: list, site_name: str):
    deliver_combined(db, user, [(site_name, articles)])
