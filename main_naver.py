"""
네이버 블로그용 원고 자동 생성

Blogger처럼 자동 발행은 하지 않는다.
네이버는 공식 글쓰기 API가 없고, 브라우저 자동화는 계정 정지 위험이 있어서
"원고 + 사진"까지만 자동으로 만들어두고 발행은 직접 한다.

실행:
    python main_naver.py

결과:
    docs/naver/YYYYMMDD-HHMM-슬러그.html  ← 복붙용 페이지
    docs/naver/YYYYMMDD-HHMM-슬러그.md    ← 백업 원고
    docs/images/*.png                      ← 사진 5장
    docs/naver/index.html                  ← 원고 목록
"""
import argparse
import json
import os
import sys
import traceback
from datetime import datetime

import config
from scripts import news, imagegen, naver_writer, naver_builder

NAVER_HISTORY_FILE = "data/naver_history.json"
HISTORY_KEEP = 200


def load_history(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_history(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries[-HISTORY_KEEP:], f, ensure_ascii=False, indent=2)


def run():
    started = datetime.now()
    print("=" * 62)
    print(f" 네이버 원고 생성  |  {started:%Y-%m-%d %H:%M}")
    print("=" * 62)

    # 1. 뉴스 수집
    print("\n[1/5] 뉴스 수집")
    candidates = news.fetch_candidates()
    if not candidates:
        print("  수집된 기사가 없습니다. 이번 회차는 건너뜁니다.")
        return 0

    # 2. 주제 선정
    print("\n[2/5] 주제 선정")
    history = load_history(NAVER_HISTORY_FILE)
    history_titles = [h.get("topic", "") for h in history if h.get("topic")]
    topic_info = naver_writer.select_topic(candidates, history_titles)
    print(f"  주제 : {topic_info['topic']}")
    print(f"  관점 : {topic_info['angle']}")

    # 3. 원고 생성
    print("\n[3/5] 원고 생성")
    article = naver_writer.write_article(topic_info)
    print("  제목 후보:")
    for i, t in enumerate(article.get("title_options", []), 1):
        print(f"    {i}. {t}")
    print(f"  최종 선택 : {article['title']}")
    print(f"  본문 길이 : {len(article['body_text'])}자")
    print(f"  태그      : {' '.join(article.get('tags', []))}")

    # 4. 사진 생성
    print("\n[4/5] 사진 생성")
    slug = naver_builder.make_slug(article["title"])
    images = imagegen.render_all(article.get("images", {}), slug)

    # 네이버 목록 썸네일은 정사각형으로 잘리므로 1:1 버전으로 교체
    images["thumbnail"] = imagegen.render_square_thumbnail(
        (article.get("images") or {}).get("thumbnail"), slug
    )

    # 5. 복붙 페이지 저장
    print("\n[5/5] 복붙 페이지 생성")
    history.append({
        "topic": topic_info["topic"],
        "title": article["title"],
        "slug": slug,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })

    result = naver_builder.save_all(article, images, topic_info, slug, history)
    save_history(NAVER_HISTORY_FILE, history)

    print(f"  원고 파일 : {result['md']}")
    print(f"  복붙 페이지: {result['url']}")
    print(f"  이력 저장 완료 (누적 {len(history)}건)")

    elapsed = (datetime.now() - started).total_seconds()
    print(f"\n소요 시간: {elapsed:.1f}초")
    print(f"\n아래 주소를 열어서 복사해 쓰세요:\n  {result['url']}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="네이버 블로그 원고 생성")
    parser.parse_args()

    try:
        return run()
    except Exception as e:
        print(f"\n{'=' * 62}")
        print(f" 실행 실패: {type(e).__name__}")
        print(f"{'=' * 62}")
        print(f"{e}\n")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
