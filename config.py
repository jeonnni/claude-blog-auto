"""
AI 한스푼 - 블로그 자동화 설정
환경변수는 GitHub Secrets에서 주입된다.
"""
import os

# ─────────────────────────────────────────────
# 블로그 기본 정보
# ─────────────────────────────────────────────
BLOG_NAME = "AI 한스푼"
BLOG_URL = "https://aispoonkr.blogspot.com"

# GitHub Pages 이미지 호스팅 주소
GITHUB_USER = "jeonnni"
GITHUB_REPO = "claude-blog-auto"
IMAGE_BASE_URL = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/images"

# ─────────────────────────────────────────────
# API 키 (GitHub Secrets)
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BLOGGER_CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID", "")
BLOGGER_CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET", "")
BLOGGER_REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN", "")
BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")

# ─────────────────────────────────────────────
# Gemini 모델 설정
# 무료 티어 모델명은 바뀔 수 있으니 여기서 한 번에 수정
# 현재 사용 가능한 모델은 https://ai.google.dev/gemini-api/docs/models 확인
# ─────────────────────────────────────────────
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)

# ─────────────────────────────────────────────
# 뉴스 수집 설정
# ─────────────────────────────────────────────
NEWS_KEYWORDS = [
    "Claude AI",
    "앤트로픽 클로드",
    "생성형 AI 활용",
    "AI 챗봇 사용법",
    "ChatGPT 제미나이 비교",
]

# Google News RSS (한국어)
NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

# 최근 며칠 이내 기사만 후보로
NEWS_MAX_AGE_DAYS = 5

# 각 키워드당 가져올 기사 수
NEWS_PER_KEYWORD = 8

# ─────────────────────────────────────────────
# 발행 이력 (중복 주제 방지)
# ─────────────────────────────────────────────
HISTORY_FILE = "data/history.json"
HISTORY_KEEP = 200  # 최근 200개 주제 기억

# ─────────────────────────────────────────────
# 이미지 설정
# ─────────────────────────────────────────────
IMAGE_DIR = "docs/images"
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675  # 16:9

# 브랜드 컬러 — 딥 차콜 (따뜻한 검정 + 크림 + 골드)
BRAND = {
    "bg": "#232120",       # 배경 (온기 있는 검정)
    "bg2": "#1C1A19",      # 배경 그라데이션 끝
    "surface": "#2A2725",  # 카드/박스 면
    "accent": "#D9A441",   # 골드 액센트
    "ink": "#F2EDE4",      # 본문 텍스트 (크림)
    "dim": "#C9C1B5",      # 흐린 텍스트
    "muted": "#8F877C",    # 보조 텍스트
    "line": "#3C3835",     # 구분선
}

# cairosvg는 시스템에 실제 설치된 폰트명과 정확히 일치해야 한글이 렌더링된다.
# GitHub Actions 워크플로우에서 fonts-noto-cjk 를 설치한다.
FONT_SANS = "Noto Sans CJK KR, NanumGothic, sans-serif"
FONT_SERIF = "Noto Serif CJK KR, serif"

# 이전 버전 호환용
FONT_FAMILY = FONT_SANS
