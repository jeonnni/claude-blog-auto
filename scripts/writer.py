"""
1) 뉴스 후보 중에서 오늘 쓸 주제를 고르고
2) 그 주제로 블로그 글 전체를 생성한다.
"""
import json

import config
from scripts import gemini


# ─────────────────────────────────────────────
# 1단계 : 주제 선정
# ─────────────────────────────────────────────
SELECT_PROMPT = """당신은 IT/AI 분야 콘텐츠 기획자입니다.

아래는 최근 수집된 뉴스 기사 목록입니다.
이 중에서 "비개발자이지만 AI에 관심 있는 일반 독자"를 위한 블로그 글 소재로
가장 적합한 것 하나를 고르세요.

[선정 기준]
- 일반인이 실제로 궁금해하거나 검색할 만한 내용
- 실용적인 정보나 활용법으로 연결할 수 있는 것
- 지나치게 기술적이거나 기업 실적/주가 위주인 것은 제외
- 아래 "이미 다룬 주제"와 겹치지 않을 것

[이미 다룬 주제]
{history}

[뉴스 후보]
{candidates}

[출력 형식]
다른 설명 없이 아래 JSON만 출력하세요.

{{
  "topic": "블로그 글의 핵심 주제를 한 문장으로",
  "angle": "이 주제를 어떤 관점/각도로 풀어낼지 한 문장으로",
  "keywords": ["검색 키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "source_title": "참고한 기사 제목",
  "source_link": "참고한 기사 링크",
  "reason": "이 주제를 고른 이유 한 문장"
}}"""


def select_topic(candidates, history):
    """뉴스 후보 중 오늘의 주제 하나를 고른다."""
    cand_text = "\n".join(
        f"{i+1}. {c['title']}\n   요약: {c['summary'][:120]}\n   링크: {c['link']}"
        for i, c in enumerate(candidates[:30])
    )
    hist_text = "\n".join(f"- {h}" for h in history[-40:]) or "(없음)"

    prompt = SELECT_PROMPT.format(history=hist_text, candidates=cand_text)
    result = gemini.call_json(prompt, temperature=0.7)

    # 필수 필드 보정
    result.setdefault("topic", "AI 활용 팁")
    result.setdefault("angle", "초보자도 바로 써먹을 수 있는 관점")
    result.setdefault("keywords", ["AI", "인공지능", "활용법"])
    result.setdefault("source_title", "")
    result.setdefault("source_link", "")
    return result


# ─────────────────────────────────────────────
# 2단계 : 본문 생성
# ─────────────────────────────────────────────
ARTICLE_PROMPT = """당신은 10년 차 전문 블로거이자 SEO 전문가입니다.
아래 조건에 맞춰 블로그 글을 작성하세요.

[블로그 정보]
- 블로그 이름: {blog_name}
- 타겟 독자: 개발자가 아니지만 AI에 관심 있는 사람
- 목적: AI 활용 꿀팁과 정보 제공

[오늘의 주제]
- 주제: {topic}
- 접근 관점: {angle}
- 핵심 키워드: {keywords}
- 참고 기사: {source_title}

[작성 규칙]
1. 제목 3개를 먼저 제시하고, 그중 가장 좋은 하나를 골라 본문을 작성합니다.
   제목에는 검색 키워드가 들어가고, 클릭하고 싶어지는 표현이어야 합니다.
2. 서론은 3줄 이내. 독자의 공감을 끌어내고 왜 읽어야 하는지 압축해서 전달합니다.
3. 본문은 소제목(H2) 3~4개 이상으로 구성하고, 필요하면 H3로 세분화합니다.
   각 소제목 아래에는 핵심 내용과 구체적인 예시를 상세히 씁니다.
   예시는 추상적으로 쓰지 말고 실제 상황이나 실제 입력/출력 예시를 보여주세요.
4. 중간중간 요약 박스나 팁 박스를 넣어 독자가 집중할 수 있게 합니다.
5. 결론에서 전체를 자연스럽게 요약하고, 댓글이나 구독 등 행동을 유도합니다.
6. 뻔한 인사말("안녕하세요 여러분!")은 쓰지 않습니다.
7. AI가 쓴 티가 나는 딱딱한 문장 대신, 사람이 직접 쓴 듯한 자연스러운 구어체를 씁니다.
   "~습니다"체를 기본으로 하되 중간중간 "~죠", "~거든요", "~인데요" 같은 표현을 섞습니다.
8. 전체 분량은 공백 포함 1500자~2000자. 너무 길게 쓰지 마세요.
9. 확실하지 않은 수치나 날짜는 단정하지 말고 "알려져 있습니다" 같은 표현을 씁니다.

[본문 HTML 규칙]
- 사용 가능 태그: h2, h3, p, ul, ol, li, strong, em, blockquote, table, thead, tbody, tr, th, td, br
- 요약/팁 박스는 이 형식으로 쓰세요:
  <blockquote class="tipbox"><strong>💡 핵심 요약</strong><br>내용</blockquote>
- 이미지는 넣지 마세요. 이미지는 나중에 자동으로 삽입됩니다.
- 본문 맨 위에 제목(h1)을 다시 쓰지 마세요.

[이미지 자리 지정]
본문 안에 이미지가 들어갈 자리 5곳을 아래 표시로 남기세요.
각 표시는 반드시 독립된 줄에 있어야 합니다.

[[IMG:thumbnail]]   ← 서론 바로 앞 (대표 이미지)
[[IMG:diagram]]     ← 개념/구조 설명이 필요한 소제목 아래
[[IMG:compare]]     ← 비교나 차이 설명이 필요한 곳
[[IMG:steps]]       ← 방법이나 순서를 설명하는 곳
[[IMG:summary]]     ← 결론 직전

[출력 형식]
다른 설명 없이 아래 JSON만 출력하세요. HTML 안의 큰따옴표는 반드시 이스케이프하세요.

{{
  "title_options": ["제목안1", "제목안2", "제목안3"],
  "title": "최종 선택한 제목",
  "labels": ["라벨1", "라벨2", "라벨3"],
  "body_html": "본문 전체 HTML",
  "images": {{
    "thumbnail": {{
      "headline": "이미지에 넣을 큰 제목 (18자 이내)",
      "sub": "부제목 (30자 이내)"
    }},
    "diagram": {{
      "title": "다이어그램 제목 (20자 이내)",
      "nodes": ["단계1", "단계2", "단계3", "단계4"],
      "caption": "한 줄 설명 (40자 이내)"
    }},
    "compare": {{
      "title": "비교표 제목 (20자 이내)",
      "col_a": "왼쪽 항목명 (10자 이내)",
      "col_b": "오른쪽 항목명 (10자 이내)",
      "rows": [
        {{"label": "비교 기준 (10자 이내)", "a": "값 (16자 이내)", "b": "값 (16자 이내)"}},
        {{"label": "비교 기준", "a": "값", "b": "값"}},
        {{"label": "비교 기준", "a": "값", "b": "값"}},
        {{"label": "비교 기준", "a": "값", "b": "값"}}
      ]
    }},
    "steps": {{
      "title": "단계 가이드 제목 (20자 이내)",
      "steps": [
        {{"name": "단계 이름 (12자 이내)", "desc": "설명 (28자 이내)"}},
        {{"name": "단계 이름", "desc": "설명"}},
        {{"name": "단계 이름", "desc": "설명"}}
      ]
    }},
    "summary": {{
      "title": "요약 카드 제목 (20자 이내)",
      "points": ["핵심 1 (30자 이내)", "핵심 2", "핵심 3"]
    }}
  }}
}}"""


def write_article(topic_info):
    """선정된 주제로 글 전체를 생성한다."""
    prompt = ARTICLE_PROMPT.format(
        blog_name=config.BLOG_NAME,
        topic=topic_info["topic"],
        angle=topic_info["angle"],
        keywords=", ".join(topic_info["keywords"]),
        source_title=topic_info.get("source_title", ""),
    )
    article = gemini.call_json(prompt, temperature=0.95)

    # 최소 검증
    if not article.get("title") or not article.get("body_html"):
        raise gemini.GeminiError("글 생성 결과에 title 또는 body_html이 없습니다.")

    article.setdefault("labels", ["AI", "인공지능"])
    article.setdefault("images", {})
    return article
