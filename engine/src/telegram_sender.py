import logging
import os

import requests

logger = logging.getLogger("trend-letter")

API_BASE = "https://api.telegram.org/bot{token}"
MAX_MSG = 4096


def _get_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "")


def send_message(text: str, chat_id: str, token: str = "") -> bool:
    """텔레그램 메시지 발송. chat_id는 사용자별."""
    token = token or _get_token()
    if not token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN 또는 chat_id 미설정")
        return False

    parts = _split(text) if len(text) > MAX_MSG else [text]
    ok = True
    for part in parts:
        if not _post_message(token, chat_id, part):
            ok = False
    return ok


def send_document(filepath: str, chat_id: str, caption: str = "", token: str = "") -> bool:
    """텔레그램 파일 발송. chat_id는 사용자별."""
    token = token or _get_token()
    if not token or not chat_id:
        return False

    url = f"{API_BASE.format(token=token)}/sendDocument"
    try:
        with open(filepath, "rb") as f:
            resp = requests.post(url, data={
                "chat_id": chat_id,
                "caption": caption[:1024] if caption else "",
            }, files={"document": f}, timeout=120)

        if resp.status_code == 200:
            logger.info(f"텔레그램 파일 전송 성공: {os.path.basename(filepath)}")
            return True
        logger.error(f"텔레그램 파일 전송 실패: {resp.status_code}")
        return False
    except Exception as e:
        logger.error(f"텔레그램 파일 전송 오류: {e}")
        return False


def _post_message(token: str, chat_id: str, text: str) -> bool:
    url = f"{API_BASE.format(token=token)}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            return True
        logger.error(f"텔레그램 메시지 전송 실패: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"텔레그램 메시지 전송 오류: {e}")
        return False


def _split(text: str) -> list[str]:
    parts = []
    while text:
        if len(text) <= MAX_MSG:
            parts.append(text)
            break
        pos = text.rfind("\n", 0, MAX_MSG)
        if pos == -1:
            pos = MAX_MSG
        parts.append(text[:pos])
        text = text[pos:].lstrip("\n")
    return parts
