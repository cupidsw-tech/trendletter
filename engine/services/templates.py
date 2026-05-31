"""뉴스레터 발송 템플릿 모음."""

TEMPLATES = {
    "compact": {
        "name": "간결한 요약",
        "description": "핵심만 불릿 포인트로 정리",
        "icon": "📋",
    },
    "detailed": {
        "name": "상세 리포트",
        "description": "섹션별 상세 분석 + 인사이트",
        "icon": "📊",
    },
    "morning_brief": {
        "name": "모닝 브리프",
        "description": "한눈에 보는 오늘의 트렌드",
        "icon": "☀️",
    },
    "card_news": {
        "name": "카드뉴스 스타일",
        "description": "한 줄 제목 + 핵심 한 문장",
        "icon": "🃏",
    },
}


def format_compact(site_name: str, category: str, articles: list) -> str:
    """간결한 요약 템플릿."""
    header = f"📋 [{category}] {site_name}\n{'─' * 30}\n"
    parts = []
    for idx, art in enumerate(articles, 1):
        summary_lines = (art.summary or "").strip().split("\n")
        brief = "\n".join(summary_lines[:3])
        parts.append(f"{idx}. {art.title}\n{brief}\n🔗 {art.url}")
    return header + "\n\n".join(parts)


def format_detailed(site_name: str, category: str, articles: list) -> str:
    """상세 리포트 템플릿."""
    header = (
        f"📊 [{category}] {site_name} — 상세 리포트\n"
        f"{'━' * 35}\n"
    )
    parts = []
    for idx, art in enumerate(articles, 1):
        part = (
            f"\n{'▸' * 3} {idx}. {art.title}\n"
            f"{'─' * 30}\n"
            f"{art.summary or '(요약 없음)'}\n\n"
            f"📎 원문: {art.url}"
        )
        parts.append(part)
    return header + "\n".join(parts)


def format_morning_brief(site_name: str, category: str, articles: list) -> str:
    """모닝 브리프 템플릿."""
    today_str = __import__("datetime").datetime.now().strftime("%Y.%m.%d")
    header = (
        f"☀️ 모닝 브리프 | {today_str}\n"
        f"[{category}] {site_name}\n"
        f"{'═' * 30}\n\n"
    )
    parts = []
    for idx, art in enumerate(articles, 1):
        # 요약에서 첫 2줄만
        summary = art.summary or ""
        lines = [l for l in summary.split("\n") if l.strip()]
        brief = " ".join(lines[:2])[:200]
        parts.append(f"• {art.title}\n  → {brief}\n  {art.url}")

    footer = f"\n\n{'─' * 30}\n오늘도 좋은 하루 되세요! ☕"
    return header + "\n\n".join(parts) + footer


def format_card_news(site_name: str, category: str, articles: list) -> str:
    """카드뉴스 스타일 템플릿."""
    header = f"🃏 [{category}] {site_name}\n\n"
    parts = []
    for idx, art in enumerate(articles, 1):
        summary = art.summary or ""
        one_liner = summary.split("\n")[0][:100] if summary else ""
        parts.append(
            f"┌───────────────────┐\n"
            f"│ {idx}. {art.title[:30]}\n"
            f"│\n"
            f"│ {one_liner}\n"
            f"│\n"
            f"│ 🔗 {art.url}\n"
            f"└───────────────────┘"
        )
    return header + "\n\n".join(parts)


FORMATTERS = {
    "compact": format_compact,
    "detailed": format_detailed,
    "morning_brief": format_morning_brief,
    "card_news": format_card_news,
}


def format_articles(template_id: str, site_name: str, category: str, articles: list) -> str:
    """템플릿 ID에 맞는 포맷터로 메시지 생성."""
    formatter = FORMATTERS.get(template_id, format_compact)
    return formatter(site_name, category, articles)
