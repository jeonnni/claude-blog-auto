"""
Google News RSS에서 최신 기사 후보를 모은다.
원문을 그대로 쓰지 않고, 제목/요약/링크만 소재로 활용한다.
"""
import re
import html
import urllib.parse
from datetime import datetime, timedelta, timezone

import feedparser

import config


def _clean(text: str) -> str:
    """RSS 설명에 섞인 HTML 태그 제거"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def fetch_candidates():
    """
    설정된 키워드로 뉴스를 모아 후보 리스트를 반환.
    반환 형식: [{"title", "summary", "link", "source", "published"}]
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.NEWS_MAX_AGE_DAYS)
    seen_titles = set()
    items = []

    for keyword in config.NEWS_KEYWORDS:
        url = config.NEWS_RSS.format(query=urllib.parse.quote(keyword))
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"  [경고] '{keyword}' 수집 실패: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= config.NEWS_PER_KEYWORD:
                break

            title = _clean(entry.get("title", ""))
            if not title or len(title) < 8:
                continue

            # 제목 중복 제거 (앞 25자 기준)
            fingerprint = title[:25]
            if fingerprint in seen_titles:
                continue

            published = _parse_date(entry)
            if published and published < cutoff:
                continue

            seen_titles.add(fingerprint)
            items.append({
                "title": title,
                "summary": _clean(entry.get("summary", ""))[:300],
                "link": entry.get("link", ""),
                "source": entry.get("source", {}).get("title", "") if isinstance(
                    entry.get("source"), dict) else "",
                "published": published.isoformat() if published else "",
                "keyword": keyword,
            })
            count += 1

        print(f"  · '{keyword}' → {count}건")

    print(f"  총 후보 {len(items)}건 수집")
    return items
