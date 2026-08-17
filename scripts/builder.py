"""
Gemini가 만든 본문 HTML에 이미지를 끼워 넣고,
블로그에 바로 올릴 수 있는 최종 HTML로 조립한다.
"""
import re
from datetime import datetime

import config

# 팁 박스 등 인라인 스타일 (Blogger는 <style> 태그를 지우는 경우가 있어 인라인으로 처리)
TIP_STYLE = (
    "background:#F1F5FF;border-left:5px solid #4F8CFF;border-radius:8px;"
    "padding:16px 20px;margin:24px 0;color:#1F2937;line-height:1.75;"
)
IMG_STYLE = (
    "width:100%;height:auto;border-radius:12px;margin:28px 0 8px;display:block;"
)
CAPTION_STYLE = (
    "text-align:center;font-size:13px;color:#8A94A6;margin:0 0 30px;"
)
SOURCE_STYLE = (
    "font-size:13px;color:#8A94A6;border-top:1px solid #E5E7EB;"
    "padding-top:14px;margin-top:36px;line-height:1.7;"
)


def _img_html(image, caption=""):
    tag = (
        f'<img src="{image["url"]}" alt="{image["alt"]}" '
        f'style="{IMG_STYLE}" loading="lazy" />'
    )
    if caption:
        tag += f'<p style="{CAPTION_STYLE}">{caption}</p>'
    return tag


def insert_images(body_html: str, images: dict, article_images: dict) -> str:
    """[[IMG:kind]] 자리표시자를 실제 이미지 태그로 교체"""
    used = set()

    def replace(match):
        kind = match.group(1).strip().lower()
        if kind not in images:
            return ""
        used.add(kind)
        caption = ""
        meta = (article_images or {}).get(kind) or {}
        if kind == "diagram":
            caption = meta.get("caption", "")
        return _img_html(images[kind], caption)

    result = re.sub(r"\[\[IMG:\s*([a-zA-Z_]+)\s*\]\]", replace, body_html)

    # 자리표시자를 빠뜨린 이미지는 글 뒤에 순서대로 붙여 5장을 보장
    leftover = [k for k in ("thumbnail", "diagram", "compare", "steps", "summary")
                if k not in used]
    if leftover:
        extra = "".join(_img_html(images[k]) for k in leftover if k in images)
        result += extra

    return result


def build_html(article: dict, images: dict, topic_info: dict) -> str:
    """최종 발행용 HTML 조립"""
    body = insert_images(
        article["body_html"],
        images,
        article.get("images", {}),
    )

    # 팁 박스에 스타일 입히기
    body = body.replace(
        '<blockquote class="tipbox">',
        f'<blockquote style="{TIP_STYLE}">',
    )

    # 남아 있을 수 있는 코드펜스 제거
    body = re.sub(r"^```html\s*|```$", "", body.strip())

    parts = [
        '<div style="line-height:1.85;font-size:16px;color:#1F2937;">',
        body,
    ]

    # 출처 표기
    source_title = topic_info.get("source_title", "")
    source_link = topic_info.get("source_link", "")
    today = datetime.now().strftime("%Y년 %m월 %d일")

    source_block = f'<div style="{SOURCE_STYLE}">'
    if source_title and source_link:
        source_block += (
            f'참고 기사: <a href="{source_link}" target="_blank" '
            f'rel="nofollow noopener">{source_title}</a><br>'
        )
    source_block += (
        f'이 글은 {today} 기준으로 작성되었습니다. '
        f'AI 서비스의 기능과 요금은 자주 바뀌므로, 실제 이용 전 공식 안내를 확인해 주세요.'
        f'</div>'
    )

    parts.append(source_block)
    parts.append("</div>")

    return "\n".join(parts)


def make_slug(title: str) -> str:
    """이미지 파일명용 슬러그 생성"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()[:28]
    return f"{stamp}-{ascii_part}" if ascii_part else stamp
