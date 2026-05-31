import logging
import os

from openai import OpenAI

from .utils import truncate

logger = logging.getLogger("trend-letter")

CHUNK_SIZE = 8000


def _get_client() -> OpenAI | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        logger.warning("OPENAI_API_KEY 미설정 — 요약 건너뜀")
        return None
    return OpenAI(api_key=key)


def summarize(text: str, title: str = "", category: str = "", is_pdf: bool = False) -> str | None:
    """텍스트를 GPT로 요약. 실패 시 None. is_pdf=True면 상세하게 요약."""
    client = _get_client()
    if not client:
        return None

    if len(text) > CHUNK_SIZE:
        return _summarize_long(client, text, title, category, is_pdf=is_pdf)
    return _call_gpt(client, text, title, category, is_pdf=is_pdf)


def _call_gpt(client: OpenAI, text: str, title: str, category: str, is_pdf: bool = False) -> str | None:
    if is_pdf:
        system = (
            "당신은 시장조사 트렌드 분석 전문가입니다.\n"
            "PDF 리포트의 핵심 내용을 상세하게 요약하세요.\n"
            "주요 데이터, 수치, 트렌드, 인사이트를 빠짐없이 정리하세요.\n"
            "불릿 포인트로 섹션별로 나눠서 정리하세요.\n"
            "한국어로 응답하세요."
        )
        max_tokens = 2000
    else:
        system = (
            "당신은 시장조사 트렌드 요약 전문가입니다.\n"
            "아침에 빠르게 읽는 '트렌드 레터' 스타일로 핵심만 간결하게 요약하세요.\n"
            "장황하지 않게, 불릿 포인트 3~5개로 정리하세요.\n"
            "한국어로 응답하세요."
        )
        max_tokens = 800
    user_msg = ""
    if category:
        user_msg += f"[카테고리: {category}]\n"
    if title:
        user_msg += f"[제목: {title}]\n\n"
    user_msg += truncate(text, 12000)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"GPT 요약 실패: {e}")
        return None


def _summarize_long(client: OpenAI, text: str, title: str, category: str, is_pdf: bool = False) -> str | None:
    """긴 텍스트 → 청크별 요약 → 통합 요약."""
    chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    partials = []
    for i, chunk in enumerate(chunks[:5]):
        logger.info(f"  청크 {i + 1}/{min(len(chunks), 5)} 요약 중")
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "주어진 텍스트의 핵심을 간결하게 요약하세요. 한국어로 응답."},
                    {"role": "user", "content": chunk},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            partials.append(resp.choices[0].message.content)
        except Exception as e:
            logger.warning(f"  청크 {i + 1} 요약 실패: {e}")

    if not partials:
        return None

    combined = "\n\n".join(partials)
    return _call_gpt(client, combined, title, category, is_pdf=is_pdf)
