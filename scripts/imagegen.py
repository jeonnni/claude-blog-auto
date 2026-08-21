"""
정보성 이미지 5종을 SVG로 그리고 PNG로 변환한다.
템플릿은 고정, 텍스트만 글마다 바뀌므로 블로그 톤이 일관되게 유지된다.

디자인: 딥 차콜 — 따뜻한 검정 배경, 크림 명조 헤드라인, 골드 액센트

1. thumbnail : 대표 썸네일 (제목 카드)
2. diagram   : 흐름도 (개념/구조)
3. compare   : 비교표
4. steps     : 단계별 가이드
5. summary   : 핵심 요약 카드
"""
import os
from xml.sax.saxutils import escape

import config

W = config.IMAGE_WIDTH
H = config.IMAGE_HEIGHT
C = config.BRAND

SANS = config.FONT_SANS
SERIF = config.FONT_SERIF


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def esc(text) -> str:
    return escape(str(text if text is not None else ""))


def cut(text, limit) -> str:
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

    if len(lines) == max_lines:
        joined = " ".join(lines)
        if len(joined) < len(text):
            lines[-1] = cut(lines[-1] + "…", per_line)

    return lines


def _base() -> str:
    """공통 배경 — 미세한 온기가 도는 검정"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bgGrad" x1="0" y1="0" x2="0.7" y2="1">
    <stop offset="0%" stop-color="{C['bg']}"/>
    <stop offset="100%" stop-color="{C['bg2']}"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bgGrad)"/>"""


def _label(text, y=152) -> str:
    """좌상단 골드 라벨 + 짧은 규칙선"""
    return f"""<rect x="88" y="{y-56}" width="58" height="4" fill="{C['accent']}"/>
<text x="88" y="{y}" font-family="{SANS}" font-size="20" font-weight="600"
 letter-spacing="5" fill="{C['accent']}">{esc(text)}</text>"""


def _footer(with_rule=True) -> str:
    """하단 구분선 + 블로그 이름"""
    rule = ""
    if with_rule:
        rule = (f'<line x1="88" y1="{H-98}" x2="{W-88}" y2="{H-98}" '
                f'stroke="{C["muted"]}" stroke-width="1" opacity="0.28"/>')
    return f"""{rule}
<text x="{W-88}" y="{H-56}" text-anchor="end" font-family="{SANS}" font-size="21"
 fill="{C['muted']}">{esc(config.BLOG_NAME)}</text>"""


def _title(text, y, size=46) -> str:
    """섹션 제목 (명조)"""
    return (f'<text x="88" y="{y}" font-family="{SERIF}" font-size="{size}" '
            f'font-weight="600" fill="{C["ink"]}">{esc(text)}</text>')


# ─────────────────────────────────────────────
# 1. 썸네일
# ─────────────────────────────────────────────
def svg_thumbnail(data):
    headline = data.get("headline") or data.get("title") or "AI 이야기"
    sub = data.get("sub", "")

    lines = wrap(headline, 13, 2)
    start_y = 350 if len(lines) == 1 else 300

    text_block = ""
    for i, line in enumerate(lines):
        text_block += (
            f'<text x="88" y="{start_y + i*96}" font-family="{SERIF}" font-size="80" '
            f'font-weight="600" fill="{C["ink"]}">{esc(line)}</text>\n'
        )

    sub_y = start_y + len(lines) * 96 + 14
    sub_block = ""
    if sub:
        sub_block = (
            f'<text x="88" y="{sub_y}" font-family="{SANS}" font-size="29" '
            f'fill="{C["muted"]}">{esc(cut(sub, 32))}</text>'
        )

    return f"""{_base()}
{_label("AI GUIDE")}
{text_block}
{sub_block}
{_footer()}
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
    gap = 30
    margin = 88
    box_w = (W - margin * 2 - gap * (count - 1)) / count
    box_h = 176
    box_y = 268

    body = ""
    for i, node in enumerate(nodes):
        x = margin + i * (box_w + gap)
        is_last = (i == count - 1)
        stroke = C["accent"] if is_last else C["line"]
        stroke_w = 1.6 if is_last else 1.2

        body += f"""<rect x="{x:.0f}" y="{box_y}" width="{box_w:.0f}" height="{box_h}"
 fill="{C['surface']}" stroke="{stroke}" stroke-width="{stroke_w}"/>
<text x="{x+26:.0f}" y="{box_y+46}" font-family="{SANS}" font-size="19"
 font-weight="700" letter-spacing="1" fill="{C['accent']}">0{i+1}</text>"""

        node_lines = wrap(node, 8, 2)
        base_y = box_y + 108 if len(node_lines) == 1 else box_y + 90
        for j, line in enumerate(node_lines):
            body += f"""
<text x="{x + box_w/2:.0f}" y="{base_y + j*40}" text-anchor="middle"
 font-family="{SERIF}" font-size="31" font-weight="600" fill="{C['ink']}">{esc(line)}</text>"""

        if not is_last:
            ax = x + box_w + gap / 2
            cy = box_y + box_h / 2
            body += f"""
<line x1="{ax-9:.0f}" y1="{cy:.0f}" x2="{ax+7:.0f}" y2="{cy:.0f}"
 stroke="{C['accent']}" stroke-width="1.6"/>
<path d="M {ax+3:.0f} {cy-5:.0f} L {ax+9:.0f} {cy:.0f} L {ax+3:.0f} {cy+5:.0f}"
 fill="none" stroke="{C['accent']}" stroke-width="1.6" stroke-linecap="round"/>"""

    caption_block = ""
    if caption:
        caption_block = (
            f'<text x="88" y="{box_y+box_h+74}" font-family="{SANS}" font-size="26" '
            f'fill="{C["muted"]}">{esc(cut(caption, 44))}</text>'
        )

    return f"""{_base()}
{_label("HOW IT WORKS", 140)}
{_title(title, 212)}
{body}
{caption_block}
{_footer()}
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

    table_x, table_y = 88, 240
    table_w = W - 176
    head_h = 62
    row_h = 72
    label_w = 268
    col_w = (table_w - label_w) / 2

    body = f"""<line x1="{table_x}" y1="{table_y}" x2="{table_x+table_w}" y2="{table_y}"
 stroke="{C['ink']}" stroke-width="1.4" opacity="0.5"/>
<text x="{table_x}" y="{table_y+42}" font-family="{SANS}" font-size="21"
 letter-spacing="1" fill="{C['muted']}">항목</text>
<text x="{table_x+label_w+col_w/2:.0f}" y="{table_y+42}" text-anchor="middle"
 font-family="{SANS}" font-size="25" font-weight="700" fill="{C['muted']}">{esc(col_a)}</text>
<text x="{table_x+label_w+col_w*1.5:.0f}" y="{table_y+42}" text-anchor="middle"
 font-family="{SANS}" font-size="25" font-weight="700" fill="{C['accent']}">{esc(col_b)}</text>
<line x1="{table_x}" y1="{table_y+head_h}" x2="{table_x+table_w}" y2="{table_y+head_h}"
 stroke="{C['line']}" stroke-width="1.2"/>"""

    for i, row in enumerate(rows):
        ry = table_y + head_h + i * row_h
        ty = ry + row_h / 2 + 10
        body += f"""
<text x="{table_x}" y="{ty:.0f}" font-family="{SANS}" font-size="24"
 fill="{C['muted']}">{esc(cut(row.get('label',''), 11))}</text>
<text x="{table_x+label_w+col_w/2:.0f}" y="{ty:.0f}" text-anchor="middle"
 font-family="{SERIF}" font-size="26" fill="{C['dim']}">{esc(cut(row.get('a',''), 14))}</text>
<text x="{table_x+label_w+col_w*1.5:.0f}" y="{ty:.0f}" text-anchor="middle"
 font-family="{SERIF}" font-size="26" font-weight="600"
 fill="{C['ink']}">{esc(cut(row.get('b',''), 14))}</text>"""

        if i < len(rows) - 1:
            body += f"""
<line x1="{table_x}" y1="{ry+row_h}" x2="{table_x+table_w}" y2="{ry+row_h}"
 stroke="{C['line']}" stroke-width="1" opacity="0.6"/>"""

    bottom = table_y + head_h + row_h * len(rows)
    body += f"""
<line x1="{table_x}" y1="{bottom}" x2="{table_x+table_w}" y2="{bottom}"
 stroke="{C['line']}" stroke-width="1.2"/>"""

    return f"""{_base()}
{_label("COMPARE", 128)}
{_title(title, 198)}
{body}
{_footer(with_rule=False)}
</svg>"""


# ─────────────────────────────────────────────
# 4. 단계 가이드
# ─────────────────────────────────────────────
def svg_steps(data):
    title = cut(data.get("title", "이렇게 하면 됩니다"), 22)
    steps = (data.get("steps") or [])[:4]
    if not steps:
        steps = [{"name": "준비", "desc": ""}]

    start_y = 250 if len(steps) <= 3 else 236
    row_h = 106 if len(steps) <= 3 else 92
    body = ""

    for i, step in enumerate(steps):
        y = start_y + i * row_h

        body += f"""<text x="88" y="{y+34}" font-family="{SERIF}" font-size="38"
 font-weight="600" fill="{C['accent']}">0{i+1}</text>
<text x="164" y="{y+30}" font-family="{SERIF}" font-size="31" font-weight="600"
 fill="{C['ink']}">{esc(cut(step.get('name',''), 13))}</text>
<text x="164" y="{y+64}" font-family="{SANS}" font-size="23"
 fill="{C['muted']}">{esc(cut(step.get('desc',''), 34))}</text>"""

        if i < len(steps) - 1:
            body += f"""
<line x1="88" y1="{y+row_h-24}" x2="{W-88}" y2="{y+row_h-24}"
 stroke="{C['line']}" stroke-width="1" opacity="0.55"/>"""

    return f"""{_base()}
{_label("STEP BY STEP", 132)}
{_title(title, 204)}
{body}
{_footer(with_rule=False)}
</svg>"""


# ─────────────────────────────────────────────
# 5. 요약 카드
# ─────────────────────────────────────────────
def svg_summary(data):
    title = cut(data.get("title", "핵심만 다시"), 22)
    points = [p for p in (data.get("points") or []) if str(p).strip()][:3]
    if not points:
        points = ["오늘 내용을 정리했습니다."]

    start_y = 278
    gap = 112
    body = ""

    for i, point in enumerate(points):
        y = start_y + i * gap
        lines = wrap(point, 30, 2)

        body += f"""<line x1="88" y1="{y-34}" x2="88" y2="{y + (len(lines)-1)*40 + 12}"
 stroke="{C['accent']}" stroke-width="2.5"/>"""

        for j, line in enumerate(lines):
            body += f"""
<text x="124" y="{y + j*40}" font-family="{SERIF}" font-size="30"
 fill="{C['ink']}">{esc(line)}</text>"""

    return f"""{_base()}
{_label("KEY POINTS", 146)}
{_title(title, 218)}
{body}
{_footer()}
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
