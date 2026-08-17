"""
Blogger API v3로 글을 발행한다.
refresh token으로 access token을 매번 새로 발급받아 사용한다.
"""
import requests

import config

TOKEN_URL = "https://oauth2.googleapis.com/token"
POSTS_URL = "https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/"


class PublishError(Exception):
    pass


def get_access_token() -> str:
    """refresh token으로 access token 발급"""
    missing = [
        name for name, value in [
            ("BLOGGER_CLIENT_ID", config.BLOGGER_CLIENT_ID),
            ("BLOGGER_CLIENT_SECRET", config.BLOGGER_CLIENT_SECRET),
            ("BLOGGER_REFRESH_TOKEN", config.BLOGGER_REFRESH_TOKEN),
            ("BLOGGER_BLOG_ID", config.BLOGGER_BLOG_ID),
        ] if not value
    ]
    if missing:
        raise PublishError(f"GitHub Secret이 비어 있습니다: {', '.join(missing)}")

    res = requests.post(TOKEN_URL, data={
        "client_id": config.BLOGGER_CLIENT_ID,
        "client_secret": config.BLOGGER_CLIENT_SECRET,
        "refresh_token": config.BLOGGER_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }, timeout=30)

    if res.status_code != 200:
        raise PublishError(
            f"토큰 갱신 실패 (HTTP {res.status_code}): {res.text[:300]}\n"
            "→ 클라이언트 ID/Secret/Refresh Token을 다시 확인하세요."
        )

    token = res.json().get("access_token")
    if not token:
        raise PublishError(f"access_token이 응답에 없습니다: {res.text[:300]}")
    return token


def publish(title: str, html: str, labels=None, draft: bool = False) -> dict:
    """글을 발행하고 결과를 반환한다."""
    token = get_access_token()
    url = POSTS_URL.format(blog_id=config.BLOGGER_BLOG_ID)

    res = requests.post(
        url,
        params={"isDraft": "true" if draft else "false"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "kind": "blogger#post",
            "title": title,
            "content": html,
            "labels": (labels or [])[:10],
        },
        timeout=60,
    )

    if res.status_code not in (200, 201):
        raise PublishError(f"발행 실패 (HTTP {res.status_code}): {res.text[:400]}")

    return res.json()
