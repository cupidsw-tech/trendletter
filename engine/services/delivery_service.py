"""발송 서비스: 웹/텔레그램/카카오톡 멀티채널 발송 + 템플릿."""
import logging
import os
from datetime import datetime

from sqlalchemy.orm import Session

from core.models import User, Article, DeliveryLog
from src.telegram_sender import send_message as tg_send, send_document as tg_doc
from src.kakao_sender import send_kakao_message
from services.templates import format_articles

logger = logging.getLogger("trend-letter")


def _cuid() -> str:
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:25]


def deliver_to_user(db: Session, user: User, articles: list[Article], site_name: str):
    """사용자에게 새 아티클 발송. 설정된 채널 모두."""
    template_id = getattr(user, "template_id", None) or "compact"

    # 웹 (항상 — DB에 이미 저장됨, 로그만)
    if user.deliver_web:
        for art in articles:
            _log(db, user.id, art.id, "web", "sent")

    # 텔레그램
    if user.deliver_telegram and user.telegram_chat_id:
        _deliver_telegram(db, user, articles, site_name, template_id)

    # 카카오톡
    if user.deliver_kakao and user.kakao_access_token:
        _deliver_kakao(db, user, articles, site_name, template_id)


def _deliver_telegram(db: Session, user: User, articles: list[Article], site_name: str, template_id: str):
    """텔레그램으로 사이트별 묶어서 발송."""
    chat_id = user.telegram_chat_id
    if not chat_id:
        return

    category = articles[0].source.category if articles and articles[0].source else ""
    full_msg = format_articles(template_id, site_name, category, articles)

    ok = tg_send(full_msg, chat_id)
    for art in articles:
        _log(db, user.id, art.id, "telegram", "sent" if ok else "failed")

    # PDF 파일 전송
    for art in articles:
        for pdf_url in (art.pdf_urls or []):
            if pdf_url.startswith("local:"):
                path = pdf_url[6:]
                if os.path.exists(path):
                    tg_doc(path, chat_id, caption=f"[{category}] {art.title}")


def _deliver_kakao(db: Session, user: User, articles: list[Article], site_name: str, template_id: str):
    """카카오톡 나에게 보내기로 발송."""
    token = user.kakao_access_token
    if not token:
        return

    category = articles[0].source.category if articles and articles[0].source else ""
    full_msg = format_articles(template_id, site_name, category, articles)

    # 카카오는 1500자 제한이라 잘라서 발송
    ok = send_kakao_message(full_msg[:1500], articles[0].url if articles else "", token)
    for art in articles:
        _log(db, user.id, art.id, "kakao", "sent" if ok else "failed")


def _log(db: Session, user_id: str, article_id: str, channel: str, status: str):
    log = DeliveryLog(
        id=_cuid(),
        user_id=user_id,
        article_id=article_id,
        channel=channel,
        status=status,
        sent_at=datetime.utcnow() if status == "sent" else None,
    )
    db.add(log)
    db.commit()
