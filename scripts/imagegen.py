"""
정보성 이미지 5종을 SVG로 그리고 PNG로 변환한다.
템플릿은 고정, 텍스트만 글마다 바뀌므로 블로그 톤이 일관되게 유지된다.

1. thumbnail : 대표 썸네일 (제목 카드)
2. diagram   : 흐름도 (개념/구조)
3. compare   : 비교표
4. steps     : 단계별 가이드
5. summary   : 핵심 요약 카드
"""
import os
import re
from xml.sax.saxutils import escape

import config

W = config.IMAGE_WIDTH
H = config.IMAGE_HEIGHT
C = config.BRAND
FONT = config.FONT_FAMILY


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def esc(text) -> str:
    """SVG에 안전한 문자열로 변환"""
    return escape(str(text if text is not None else ""))


def cut(text, limit) -> str:
    """길면 잘라내고 말줄임"""
    text = str(text if text is not None else "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def wrap(text, per_line, max_lines=2):
    """글자 수 기준 줄바꿈 (한글은 폭이 일정해서 이 방식이 잘 맞음)"""
    text = str(text if text is not None else "").strip()
    words = text.split()
    lines, current = [], ""

    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= per_line:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if not lines:
        lines = [text[:per_line]]

    # 넘치는 분량은 마지막 줄에 말줄임 처리
    if len(lines) == max_lines:
        joined = " ".join(lines)
        if len(joined) < len(text):
            lines[-1] = cut(lines[-1] + "…", per_line)

    return lines


def _base(extra_defs="") -> str:
    """모든 이미지 공통 배경 + 그라데이션 정의"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{C['bg']}"/>
    <stop offset="100%" stop-color="#141B2B"/>
  </linearGradient>
  <linearGradient id="accGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{C['accent']}"/>
    <stop offset="100%" stop-color="{C['accent2']}"/>
  </linearGradient>
  {extra_defs}
</defs>
<rect width="{W}" height="{H}" fill="url(#bgGrad)"/>
<circle cx="{W-90}" cy="70" r="220" fill="{C['accent']}" opacity="0.07"/>
<circle cx="70" cy="{H-60}" r="180" fill="{C['accent2']}" opacity="0.06"/>
<rect x="0" y="0" width="{W}" height="6" fill="url(#accGrad)"/>"""


def _brand_mark(y=None) -> str:
    """우측 하단 블로그 이름"""
    y = y or H - 34
    return f"""<text x="{W-48}" y="{y}" text-anchor="end" font-family="{FONT}"
 font-size="22" fill="{C['muted']}" opacity="0.75">{esc(config.BLOG_NAME)}</text>"""


def _tag(x, y, label) -> str:
    """좌측 상단 카테고리 뱃지"""
    width = len(label) * 20 + 44
    return f"""<rect x="{x}" y="{y}" width="{width}" height="46" rx="23" fill="{C['accent']}" opacity="0.16"/>
<text x="{x+22}" y="{y+31}" font-family="{FONT}" font-size="22" font-weight="700"
 fill="{C['accent']}">{esc(label)}</text>"""


# ─────────────────────────────────────────────
# 1. 썸네일
# ─────────────────────────────────────────────
def svg_thumbnail(data):
    headline = data.get("headline") or data.get("title") or "AI 이야기"
    sub = data.get("sub", "")

    lines = wrap(headline, 15, 2)
    start_y = 300 if len(lines) == 1 else 250
    text_block = ""
    for i, line in enumerate(lines):
        text_block += (
            f'<text x="80" y="{start_y + i*92}" font-family="{FONT}" font-size="76" '
            f'font-weight="800" fill="{C["text"]}">{esc(line)}</text>\n'
        )

    sub_y = start_y + len(lines) * 92 + 28
    sub_block = ""
    if sub:
        sub_block = (
            f'<text x="80" y="{sub_y}" font-family="{FONT}" font-size="32" '
            f'fill="{C["muted"]}">{esc(cut(sub, 32))}</text>'
        )

    return f"""{_base()}
{_tag(80, 96, "AI 인사이트")}
<rect x="80" y="{start_y-92}" width="76" height="8" rx="4" fill="url(#accGrad)"/>
{text_block}
{sub_block}
{_brand_mark()}
</svg>"""


# ─────────────────────────────────────────────
# 2. 흐름도
# ─────────────────────────────────────────────
def svg_diagram(data):
    title = cut(data.get("title", "동작 방식"), 22)
    nodes = [n for n in (data.get("nodes") or []) if str(n).strip()][:4]
    if len(nodes) < 2:
        nodes = ["입력", "처리", "결과"]
    caption = data.get("caption", "")

    count = len(nodes)
    gap = 34
    margin = 80
    box_w = (W - margin * 2 - gap * (count - 1)) / count
    box_h = 190
    box_y = 250

    body = ""
    for i, node in enumerate(nodes):
        x = margin + i * (box_w + gap)
        is_last = (i == count - 1)
        fill = C["surface"]
        stroke = C["accent"] if is_last else C["line"]

        body += f"""<rect x="{x:.0f}" y="{box_y}" width="{box_w:.0f}" height="{box_h}" rx="18"
 fill="{fill}" stroke="{stroke}" stroke-width="2"/>
<circle cx="{x+34:.0f}" cy="{box_y+40}" r="19" fill="{C['accent']}" opacity="0.18"/>
<text x="{x+34:.0f}" y="{box_y+48}" text-anchor="middle" font-family="{FONT}"
 font-size="20" font-weight="800" fill="{C['accent']}">{i+1}</text>"""

        for j, line in enumerate(wrap(node, 9, 2)):
            body += f"""
<text x="{x + box_w/2:.0f}" y="{box_y + 110 + j*40}" text-anchor="middle"
 font-family="{FONT}" font-size="30" font-weight="700" fill="{C['text']}">{esc(line)}</text>"""

        if not is_last:
            ax = x + box_w + gap / 2
            body += f"""
<path d="M {ax-11:.0f} {box_y+box_h/2-13:.0f} L {ax+9:.0f} {box_y+box_h/2:.0f} L {ax-11:.0f} {box_y+box_h/2+13:.0f} Z"
 fill="{C['accent']}" opacity="0.85"/>"""

    caption_block = ""
    if caption:
        caption_block = (
            f'<text x="{W/2:.0f}" y="{box_y+box_h+78}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="27" fill="{C["muted"]}">{esc(cut(caption, 42))}</text>'
        )

    return f"""{_base()}
{_tag(80, 86, "구조 한눈에")}
<text x="80" y="196" font-family="{FONT}" font-size="46" font-weight="800"
 fill="{C['text']}">{esc(title)}</text>
{body}
{caption_block}
{_brand_mark()}
</svg>"""


# ─────────────────────────────────────────────
# 3. 비교표
# ─────────────────────────────────────────────
def svg_compare(data):
    title = cut(data.get("title", "무엇이 다를까"), 22)
    col_a = cut(data.get("col_a", "A"), 11)
    col_b = cut(data.get("col_b", "B"), 11)
    rows = (data.get("rows") or [])[:4]
    if not rows:
        rows = [{"label": "항목", "a": "-", "b": "-"}]

    table_x, table_y = 80, 208
    table_w = W - 160
    head_h = 66
    row_h = 76
    label_w = 300
    col_w = (table_w - label_w) / 2

    body = f"""<rect x="{table_x}" y="{table_y}" width="{table_w}" height="{head_h + row_h*len(rows)}"
 rx="18" fill="{C['surface']}" stroke="{C['line']}" stroke-width="2"/>
<rect x="{table_x}" y="{table_y}" width="{table_w}" height="{head_h}" rx="18" fill="{C['accent']}" opacity="0.14"/>
<rect x="{table_x}" y="{table_y+head_h-18}" width="{table_w}" height="18" fill="{C['accent']}" opacity="0.14"/>
<text x="{table_x+label_w/2:.0f}" y="{table_y+44}" text-anchor="middle" font-family="{FONT}"
 font-size="26" font-weight="700" fill="{C['muted']}">항목</text>
<text x="{table_x+label_w+col_w/2:.0f}" y="{table_y+44}" text-anchor="middle" font-family="{FONT}"
 font-size="28" font-weight="800" fill="{C['accent']}">{esc(col_a)}</text>
<text x="{table_x+label_w+col_w*1.5:.0f}" y="{table_y+44}" text-anchor="middle" font-family="{FONT}"
 font-size="28" font-weight="800" fill="{C['accent2']}">{esc(col_b)}</text>
<line x1="{table_x+label_w}" y1="{table_y}" x2="{table_x+label_w}" y2="{table_y+head_h+row_h*len(rows)}"
 stroke="{C['line']}" stroke-width="2"/>
<line x1="{table_x+label_w+col_w:.0f}" y1="{table_y}" x2="{table_x+label_w+col_w:.0f}"
 y2="{table_y+head_h+row_h*len(rows)}" stroke="{C['line']}" stroke-width="2"/>"""

    for i, row in enumerate(rows):
        ry = table_y + head_h + i * row_h
        if i > 0:
            body += f"""
<line x1="{table_x}" y1="{ry}" x2="{table_x+table_w}" y2="{ry}" stroke="{C['line']}" stroke-width="1.5"/>"""
        ty = ry + row_h / 2 + 11
        body += f"""
<text x="{table_x+28}" y="{ty:.0f}" font-family="{FONT}" font-size="26" font-weight="700"
 fill="{C['muted']}">{esc(cut(row.get('label',''), 11))}</text>
<text x="{table_x+label_w+col_w/2:.0f}" y="{ty:.0f}" text-anchor="middle" font-family="{FONT}"
 font-size="26" fill="{C['text']}">{esc(cut(row.get('a',''), 15))}</text>
<text x="{table_x+label_w+col_w*1.5:.0f}" y="{ty:.0f}" text-anchor="middle" font-family="{FONT}"
 font-size="26" fill="{C['text']}">{esc(cut(row.get('b',''), 15))}</text>"""

    return f"""{_base()}
{_tag(80, 74, "비교 정리")}
<text x="80" y="184" font-family="{FONT}" font-size="46" font-weight="800"
 fill="{C['text']}">{esc(title)}</text>
{body}
{_brand_mark()}
</svg>"""


# ─────────────────────────────────────────────
# 4. 단계 가이드
# ─────────────────────────────────────────────
def svg_steps(data):
    title = cut(data.get("title", "이렇게 하면 됩니다"), 22)
    steps = (data.get("steps") or [])[:4]
    if not steps:
        steps = [{"name": "준비", "desc": ""}]

    # 단계 수에 따라 간격을 조절해 하단 여백 확보
    start_y = 230 if len(steps) <= 3 else 214
    row_h = 112 if len(steps) <= 3 else 98
    body = ""

    for i, step in enumerate(steps):
        y = start_y + i * row_h
        body += f"""<rect x="80" y="{y}" width="{W-160}" height="82" rx="16"
 fill="{C['surface']}" stroke="{C['line']}" stroke-width="2"/>
<circle cx="136" cy="{y+41}" r="27" fill="url(#accGrad)"/>
<text x="136" y="{y+51}" text-anchor="middle" font-family="{FONT}" font-size="27"
 font-weight="800" fill="#FFFFFF">{i+1}</text>
<text x="188" y="{y+38}" font-family="{FONT}" font-size="30" font-weight="700"
 fill="{C['text']}">{esc(cut(step.get('name',''), 13))}</text>
<text x="188" y="{y+69}" font-family="{FONT}" font-size="24"
 fill="{C['muted']}">{esc(cut(step.get('desc',''), 34))}</text>"""

        if i < len(steps) - 1:
            body += f"""
<line x1="136" y1="{y+82}" x2="136" y2="{y+row_h}" stroke="{C['line']}"
 stroke-width="3" stroke-dasharray="5 6"/>"""

    return f"""{_base()}
{_tag(80, 84, "단계별 가이드")}
<text x="80" y="196" font-family="{FONT}" font-size="46" font-weight="800"
 fill="{C['text']}">{esc(title)}</text>
{body}
{_brand_mark()}
</svg>"""


# ─────────────────────────────────────────────
# 5. 요약 카드
# ─────────────────────────────────────────────
def svg_summary(data):
    title = cut(data.get("title", "핵심만 다시"), 22)
    points = [p for p in (data.get("points") or []) if str(p).strip()][:3]
    if not points:
        points = ["오늘 내용을 정리했습니다."]

    start_y = 262
    gap = 118
    body = ""

    for i, point in enumerate(points):
        y = start_y + i * gap
        body += f"""<rect x="80" y="{y}" width="{W-160}" height="96" rx="16"
 fill="{C['surface']}" stroke="{C['line']}" stroke-width="2"/>
<rect x="80" y="{y}" width="7" height="96" rx="4" fill="url(#accGrad)"/>
<circle cx="146" cy="{y+48}" r="21" fill="{C['good']}" opacity="0.18"/>
<path d="M 138 {y+48} L 144 {y+55} L 155 {y+41}" stroke="{C['good']}" stroke-width="4"
 fill="none" stroke-linecap="round" stroke-linejoin="round"/>"""

        for j, line in enumerate(wrap(point, 32, 2)):
            ty = y + (58 if len(wrap(point, 32, 2)) == 1 else 42) + j * 36
            body += f"""
<text x="188" y="{ty}" font-family="{FONT}" font-size="28" font-weight="600"
 fill="{C['text']}">{esc(line)}</text>"""

    return f"""{_base()}
{_tag(80, 92, "핵심 요약")}
<text x="80" y="206" font-family="{FONT}" font-size="46" font-weight="800"
 fill="{C['text']}">{esc(title)}</text>
{body}
{_brand_mark()}
</svg>"""


# ─────────────────────────────────────────────
# 렌더링
# ─────────────────────────────────────────────
BUILDERS = {
    "thumbnail": svg_thumbnail,
    "diagram": svg_diagram,
    "compare": svg_compare,
    "steps": svg_steps,
    "summary": svg_summary,
}

ALT_TEXT = {
    "thumbnail": "대표 이미지",
    "diagram": "동작 구조 다이어그램",
    "compare": "비교표",
    "steps": "단계별 가이드",
    "summary": "핵심 요약",
}


def render_all(images_data, slug):
    """
    5종 이미지를 만들어 PNG로 저장.
    반환: {"thumbnail": {"file": "...", "url": "...", "alt": "..."}, ...}
    """
    try:
        import cairosvg
    except ImportError:
        raise RuntimeError("cairosvg가 필요합니다:  pip install cairosvg")

    os.makedirs(config.IMAGE_DIR, exist_ok=True)
    result = {}

    for kind, builder in BUILDERS.items():
        data = images_data.get(kind) or {}
        try:
            svg = builder(data)
        except Exception as e:
            print(f"    [경고] {kind} SVG 생성 실패, 기본값 사용: {e}")
            svg = builder({})

        filename = f"{slug}-{kind}.png"
        path = os.path.join(config.IMAGE_DIR, filename)

        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=path,
            output_width=W,
            output_height=H,
        )

        result[kind] = {
            "file": path,
            "url": f"{config.IMAGE_BASE_URL}/{filename}",
            "alt": ALT_TEXT[kind],
        }
        print(f"    · {filename}")

    return result
