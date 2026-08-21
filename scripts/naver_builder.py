"""
네이버 블로그에 복붙하기 좋은 형태로 결과물을 만든다.

두 가지를 만든다:
  1) 원고 텍스트 파일 (.md)  — 백업 및 이력용
  2) 복붙용 HTML 페이지      — GitHub Pages에서 열어 바로 복사
"""
import os
import re
from datetime import datetime
from xml.sax.saxutils import escape

import config

NAVER_DIR = "docs/naver"


def make_slug(title: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()[:24]
    return f"{stamp}-{ascii_part}" if ascii_part else stamp


def split_by_images(body_text: str):
    """
    본문을 [[IMG:kind]] 기준으로 쪼개서
    [("text", "내용"), ("image", "thumbnail"), ...] 형태로 반환
    """
    parts = []
    pattern = re.compile(r"\[\[IMG:\s*([a-zA-Z_]+)\s*\]\]")
    last = 0

    for match in pattern.finditer(body_text):
        text_chunk = body_text[last:match.start()].strip()
        if text_chunk:
            parts.append(("text", text_chunk))
        parts.append(("image", match.group(1).strip().lower()))
        last = match.end()

    tail = body_text[last:].strip()
    if tail:
        parts.append(("text", tail))

    return parts


def build_markdown(article, images, topic_info, slug):
    """백업용 마크다운 원고"""
    lines = [
        f"# {article['title']}",
        "",
        "## 제목 후보",
    ]
    for i, t in enumerate(article.get("title_options", []), 1):
        lines.append(f"{i}. {t}")

    lines += [
        "",
        "## 태그",
        " ".join(f"#{t.replace(' ', '')}" for t in article.get("tags", [])),
        "",
        "## 본문",
        "",
    ]

    for kind, value in split_by_images(article["body_text"]):
        if kind == "text":
            lines.append(value)
            lines.append("")
        else:
            img = images.get(value)
            if img:
                lines.append(f"![{img['alt']}]({img['url']})")
                lines.append(f"`사진 파일: {os.path.basename(img['file'])}`")
                lines.append("")

    source_title = topic_info.get("source_title", "")
    source_link = topic_info.get("source_link", "")
    if source_title:
        lines += ["---", "", f"참고 기사: {source_title}", source_link, ""]

    return "\n".join(lines)


def build_paste_page(article, images, topic_info, slug):
    """GitHub Pages에서 열어 바로 복사할 수 있는 HTML"""
    title = escape(article["title"])
    today = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    # 제목 후보
    title_opts = "".join(
        f'<li><span class="t">{escape(t)}</span>'
        f'<button class="copy" data-copy="{escape(t)}">복사</button></li>'
        for t in article.get("title_options", [])
    )

    # 태그
    tag_line = " ".join(f"#{t.replace(' ', '')}" for t in article.get("tags", []))

    # 본문 블록
    blocks = []
    img_no = 0
    for kind, value in split_by_images(article["body_text"]):
        if kind == "text":
            html_text = escape(value).replace("\n", "<br>")
            blocks.append(
                f'<div class="block text">'
                f'<div class="body">{html_text}</div>'
                f'<button class="copy" data-copy="{escape(value)}">이 부분 복사</button>'
                f'</div>'
            )
        else:
            img = images.get(value)
            if not img:
                continue
            img_no += 1
            fname = os.path.basename(img["file"])
            blocks.append(
                f'<div class="block img">'
                f'<div class="imgno">사진 {img_no}</div>'
                f'<img src="../images/{fname}" alt="{escape(img["alt"])}">'
                f'<div class="fname">{fname}</div>'
                f'<a class="dl" href="../images/{fname}" download>사진 저장</a>'
                f'</div>'
            )

    body_blocks = "\n".join(blocks)

    # 전체 본문 (사진 자리 표시 포함)
    full_text = article["body_text"]
    for kind in ("thumbnail", "diagram", "compare", "steps", "summary"):
        full_text = full_text.replace(f"[[IMG:{kind}]]", f"( 사진 여기 — {kind} )")

    source_title = escape(topic_info.get("source_title", ""))
    source_link = escape(topic_info.get("source_link", ""))
    source_html = ""
    if source_title:
        source_html = (
            f'<div class="source">참고 기사: '
            f'<a href="{source_link}" target="_blank" rel="noopener">{source_title}</a></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — 네이버 원고</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px 16px 80px;
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
                 "Malgun Gothic", sans-serif;
    background: #F6F7F9; color: #1F2937; line-height: 1.75;
  }}
  .wrap {{ max-width: 720px; margin: 0 auto; }}
  .head {{
    background: #03C75A; color: #fff; padding: 20px 22px;
    border-radius: 14px; margin-bottom: 20px;
  }}
  .head h1 {{ margin: 0 0 6px; font-size: 20px; line-height: 1.45; }}
  .head .date {{ font-size: 13px; opacity: .9; }}
  .card {{
    background: #fff; border-radius: 14px; padding: 18px 20px;
    margin-bottom: 16px; border: 1px solid #E5E7EB;
  }}
  .card h2 {{
    margin: 0 0 12px; font-size: 15px; color: #6B7280;
    font-weight: 700; letter-spacing: .3px;
  }}
  ul {{ margin: 0; padding: 0; list-style: none; }}
  ul li {{
    display: flex; align-items: center; gap: 10px;
    padding: 9px 0; border-bottom: 1px solid #F3F4F6;
  }}
  ul li:last-child {{ border-bottom: 0; }}
  ul li .t {{ flex: 1; font-size: 15px; }}
  .copy {{
    border: 0; background: #EEF2FF; color: #4F46E5;
    padding: 7px 13px; border-radius: 8px; font-size: 13px;
    cursor: pointer; white-space: nowrap; font-weight: 600;
  }}
  .copy:hover {{ background: #E0E7FF; }}
  .copy.done {{ background: #DCFCE7; color: #16A34A; }}
  .tags {{ color: #2563EB; font-size: 14px; word-break: keep-all; }}
  .block {{
    background: #fff; border: 1px solid #E5E7EB;
    border-radius: 14px; padding: 16px 18px; margin-bottom: 12px;
  }}
  .block.text .body {{ font-size: 15.5px; margin-bottom: 12px; }}
  .block.img {{ text-align: center; background: #FAFBFC; }}
  .block.img img {{
    width: 100%; height: auto; border-radius: 10px; display: block;
  }}
  .imgno {{
    font-size: 12px; color: #9CA3AF; margin-bottom: 8px;
    font-weight: 700; letter-spacing: .5px;
  }}
  .fname {{
    font-size: 12px; color: #9CA3AF; margin-top: 8px;
    font-family: ui-monospace, Menlo, monospace;
  }}
  .dl {{
    display: inline-block; margin-top: 10px; padding: 8px 16px;
    background: #F3F4F6; color: #374151; border-radius: 8px;
    text-decoration: none; font-size: 13px; font-weight: 600;
  }}
  .source {{
    font-size: 13px; color: #9CA3AF; margin-top: 22px;
    padding-top: 14px; border-top: 1px solid #E5E7EB;
  }}
  .source a {{ color: #6B7280; }}
  .allbar {{
    position: fixed; left: 0; right: 0; bottom: 0;
    background: #fff; border-top: 1px solid #E5E7EB;
    padding: 12px 16px; text-align: center;
  }}
  .allbar button {{
    width: 100%; max-width: 720px; padding: 14px;
    background: #03C75A; color: #fff; border: 0;
    border-radius: 10px; font-size: 15px; font-weight: 700; cursor: pointer;
  }}
  .allbar button.done {{ background: #16A34A; }}
  .guide {{
    background: #FFFBEB; border: 1px solid #FDE68A;
    border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
    font-size: 14px; color: #92400E;
  }}
  .guide b {{ display: block; margin-bottom: 6px; }}
</style>
</head>
<body>
<div class="wrap">

  <div class="head">
    <h1>{title}</h1>
    <div class="date">{today} 생성</div>
  </div>

  <div class="guide">
    <b>이렇게 쓰면 됩니다</b>
    네이버 블로그 글쓰기를 연 뒤, 아래 본문을 순서대로 복사해 붙여넣고
    사진 자리에는 저장한 이미지를 올리면 됩니다.
  </div>

  <div class="card">
    <h2>제목 후보</h2>
    <ul>{title_opts}</ul>
  </div>

  <div class="card">
    <h2>태그</h2>
    <div class="tags">{escape(tag_line)}</div>
    <div style="margin-top:12px">
      <button class="copy" data-copy="{escape(tag_line)}">태그 전체 복사</button>
    </div>
  </div>

  <div class="card">
    <h2>본문</h2>
  </div>

  {body_blocks}

  {source_html}
</div>

<div class="allbar">
  <button id="all" data-copy="{escape(full_text)}">본문 전체 복사</button>
</div>

<script>
document.addEventListener('click', function (e) {{
  var btn = e.target.closest('[data-copy]');
  if (!btn) return;
  var text = btn.getAttribute('data-copy');
  var original = btn.textContent;

  function done() {{
    btn.textContent = '복사됨';
    btn.classList.add('done');
    setTimeout(function () {{
      btn.textContent = original;
      btn.classList.remove('done');
    }}, 1400);
  }}

  if (navigator.clipboard && window.isSecureContext) {{
    navigator.clipboard.writeText(text).then(done);
  }} else {{
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {{ document.execCommand('copy'); done(); }} catch (err) {{}}
    document.body.removeChild(ta);
  }}
}});
</script>
</body>
</html>"""


def build_index(entries):
    """최근 원고 목록 페이지"""
    items = "".join(
        f'<li><a href="{escape(e["slug"])}.html">{escape(e["title"])}</a>'
        f'<span>{escape(e["created_at"][:16].replace("T", " "))}</span></li>'
        for e in reversed(entries[-40:])
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>네이버 원고 목록</title>
<style>
  body {{
    margin:0; padding:28px 16px;
    font-family:-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
                "Malgun Gothic", sans-serif;
    background:#F6F7F9; color:#1F2937;
  }}
  .wrap {{ max-width:720px; margin:0 auto; }}
  h1 {{ font-size:20px; margin:0 0 20px; }}
  ul {{ list-style:none; margin:0; padding:0; }}
  li {{
    background:#fff; border:1px solid #E5E7EB; border-radius:12px;
    padding:16px 18px; margin-bottom:10px;
    display:flex; align-items:center; gap:12px;
  }}
  li a {{ flex:1; color:#1F2937; text-decoration:none; font-size:15px; font-weight:600; }}
  li span {{ font-size:12px; color:#9CA3AF; white-space:nowrap; }}
  .empty {{ color:#9CA3AF; text-align:center; padding:40px 0; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>네이버 원고 목록</h1>
  <ul>{items or '<div class="empty">아직 생성된 원고가 없습니다.</div>'}</ul>
</div>
</body>
</html>"""


def save_all(article, images, topic_info, slug, naver_history):
    """원고 파일 + 복붙 페이지 + 목록 페이지를 저장"""
    os.makedirs(NAVER_DIR, exist_ok=True)

    md_path = os.path.join(NAVER_DIR, f"{slug}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown(article, images, topic_info, slug))

    html_path = os.path.join(NAVER_DIR, f"{slug}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_paste_page(article, images, topic_info, slug))

    index_path = os.path.join(NAVER_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(build_index(naver_history))

    page_url = (
        f"https://{config.GITHUB_USER}.github.io/"
        f"{config.GITHUB_REPO}/naver/{slug}.html"
    )
    return {"md": md_path, "html": html_path, "url": page_url}
