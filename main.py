"""
AI 한스푼 — 블로그 자동 발행 메인 스크립트

실행 순서:
  1) Google News RSS에서 최신 기사 수집
  2) Gemini로 오늘의 주제 선정 (이미 쓴 주제는 제외)
  3) Gemini로 블로그 글 생성
  4) SVG 템플릿으로 정보성 이미지 5장 생성
  5) Blogger에 발행
  6) 발행 이력 저장

옵션:
  python main.py --draft   → 실제 발행 대신 임시저장(초안)으로
  python main.py --dry-run → 발행하지 않고 결과만 확인
"""
import argparse
import json
import os
import sys
import traceback
from datetime import datetime

import config
from scripts import news, writer, imagegen, builder, publisher


# ─────────────────────────────────────────────
# 발행 이력
# ─────────────────────────────────────────────
def load_history():
    if not os.path.exists(config.HISTORY_FILE):
        return []
    try:
        with open(config.HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_history(entries):
    os.makedirs(os.path.dirname(config.HISTORY_FILE), exist_ok=True)
    with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries[-config.HISTORY_KEEP:], f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def run(draft=False, dry_run=False):
    started = datetime.now()
    print("=" * 62)
    print(f" {config.BLOG_NAME} 자동 발행  |  {started:%Y-%m-%d %H:%M}")
    print("=" * 62)

    # 1. 뉴스 수집
    print("\n[1/6] 뉴스 수집")
    candidates = news.fetch_candidates()
    if not candidates:
        print("  수집된 기사가 없습니다. 이번 회차는 건너뜁니다.")
        return 0

    # 2. 주제 선정
    print("\n[2/6] 주제 선정")
    history = load_history()
    history_titles = [h.get("topic", "") for h in history if h.get("topic")]
    topic_info = writer.select_topic(candidates, history_titles)
    print(f"  주제 : {topic_info['topic']}")
    print(f"  관점 : {topic_info['angle']}")
    print(f"  이유 : {topic_info.get('reason', '-')}")

    # 3. 글 생성
    print("\n[3/6] 본문 생성")
    article = writer.write_article(topic_info)
    print(f"  제목 후보:")
    for i, t in enumerate(article.get("title_options", []), 1):
        print(f"    {i}. {t}")
    print(f"  최종 선택 : {article['title']}")
    print(f"  본문 길이 : {len(article['body_html'])}자")
    print(f"  라벨      : {', '.join(article.get('labels', []))}")

    # 4. 이미지 생성
    print("\n[4/6] 이미지 생성")
    slug = builder.make_slug(article["title"])
    images = imagegen.render_all(article.get("images", {}), slug)

    # 5. HTML 조립
    print("\n[5/6] HTML 조립")
    html = builder.build_html(article, images, topic_info)
    print(f"  최종 HTML 길이 : {len(html)}자")

    if dry_run:
        os.makedirs("data", exist_ok=True)
        preview = f"data/preview-{slug}.html"
        with open(preview, "w", encoding="utf-8") as f:
            f.write(f"<meta charset='utf-8'><h1>{article['title']}</h1>\n{html}")
        print(f"\n[6/6] dry-run 모드 — 발행하지 않았습니다.")
        print(f"  미리보기 파일: {preview}")
        return 0

    # 6. 발행
    print("\n[6/6] Blogger 발행")
    result = publisher.publish(
        title=article["title"],
        html=html,
        labels=article.get("labels", []),
        draft=draft,
    )
    post_url = result.get("url", "(초안으로 저장됨)")
    print(f"  상태 : {'초안 저장' if draft else '발행 완료'}")
    print(f"  주소 : {post_url}")

    # 이력 저장
    history.append({
        "topic": topic_info["topic"],
        "title": article["title"],
        "url": post_url,
        "slug": slug,
        "published_at": datetime.now().isoformat(timespec="seconds"),
    })
    save_history(history)
    print(f"  이력 저장 완료 (누적 {len(history)}건)")

    elapsed = (datetime.now() - started).total_seconds()
    print(f"\n소요 시간: {elapsed:.1f}초")
    return 0


def main():
    parser = argparse.ArgumentParser(description="AI 한스푼 블로그 자동 발행")
    parser.add_argument("--draft", action="store_true", help="초안으로 저장")
    parser.add_argument("--dry-run", action="store_true", help="발행하지 않고 미리보기만")
    args = parser.parse_args()

    try:
        return run(draft=args.draft, dry_run=args.dry_run)
    except Exception as e:
        print(f"\n{'=' * 62}")
        print(f" 실행 실패: {type(e).__name__}")
        print(f"{'=' * 62}")
        print(f"{e}\n")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
