"""카카오톡 나에게 보내기 API."""
import json
import logging

import requests

logger = logging.getLogger("trend-letter")


def send_kakao_message(text: str, link_url: str, access_token: str) -> bool:
    """카카오톡 나에게 보내기로 텍스트 메시지 발송."""
    if not access_token:
        logger.error("카카오톡 access_token 없음")
        return False

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}

    template = {
        "object_type": "text",
        "text": text[:1500],  # 카카오톡 최대 길이
        "link": {
            "web_url": link_url,
            "mobile_web_url": link_url,
        },
        "button_title": "자세히 보기",
    }

    try:
        resp = requests.post(
            url,
            data={"template_object": json.dumps(template)},
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 200:
            logger.info("카카오톡 발송 성공")
            return True
        logger.error(f"카카오톡 발송 실패: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"카카오톡 발송 오류: {e}")
        return False


def refresh_kakao_token(refresh_token: str, client_id: str) -> dict | None:
    """카카오 리프레시 토큰으로 새 액세스 토큰 발급."""
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    try:
        resp = requests.post(url, data=data, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        logger.error(f"카카오 토큰 갱신 실패: {resp.status_code}")
        return None
    except Exception as e:
        logger.error(f"카카오 토큰 갱신 오류: {e}")
        return None
