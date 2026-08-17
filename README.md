# AI 한스푼 — 블로그 자동 발행

Google News에서 최신 AI 소식을 수집해 블로그 글을 작성하고,
정보성 이미지 5장을 함께 만들어 Blogger에 자동 발행합니다.

- 블로그: https://aispoonkr.blogspot.com
- 발행 주기: 4시간마다 (하루 6개)
- 글 작성: Google Gemini API (무료 티어)
- 이미지: SVG 템플릿 5종 → PNG 자동 생성

---

## 동작 흐름

```
GitHub Actions (4시간마다)
      ↓
1. Google News RSS 수집        scripts/news.py
2. 오늘의 주제 선정 (Gemini)    scripts/writer.py
3. 블로그 글 생성 (Gemini)      scripts/writer.py
4. 이미지 5장 생성 (SVG→PNG)    scripts/imagegen.py
5. HTML 조립 + 이미지 삽입      scripts/builder.py
6. Blogger 발행                scripts/publisher.py
7. 이미지·이력을 저장소에 커밋
```

이미지는 GitHub Pages(`docs/images/`)에 호스팅되고,
글에는 그 주소가 삽입됩니다.

---

## 최초 설정

### 1. 저장소를 Public으로 변경

GitHub Pages 무료 사용은 Public 저장소에서만 가능합니다.
Secrets는 Public 저장소에서도 암호화되어 노출되지 않습니다.

`Settings → General → 맨 아래 Danger Zone → Change visibility → Public`

### 2. GitHub Pages 활성화

`Settings → Pages`

- Source: **Deploy from a branch**
- Branch: **main** / 폴더: **/docs**
- Save

몇 분 뒤 `https://jeonnni.github.io/claude-blog-auto/` 가 열리면 성공입니다.

### 3. Refresh Token 발급 (내 PC에서 1회)

```bash
pip install google-auth-oauthlib
python get_token.py
```

브라우저에서 구글 로그인 → 허용 → 터미널에 출력된 토큰을 복사합니다.

> "앱이 확인되지 않았습니다" 화면이 나오면
> 고급 → 안전하지 않은 페이지로 이동 을 눌러 진행하면 됩니다.

### 4. GitHub Secrets 등록

`Settings → Secrets and variables → Actions → New repository secret`

| 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio에서 발급한 키 |
| `BLOGGER_CLIENT_ID` | `...apps.googleusercontent.com` |
| `BLOGGER_CLIENT_SECRET` | OAuth 클라이언트 보안 비밀 |
| `BLOGGER_REFRESH_TOKEN` | 3단계에서 발급한 토큰 |
| `BLOGGER_BLOG_ID` | 블로거 설정 URL 뒤 숫자 |

### 5. 첫 실행 테스트

`Actions → 블로그 자동 발행 → Run workflow`

처음에는 **draft** 모드로 실행해서 결과를 확인한 뒤,
만족스러우면 **publish**로 바꾸세요.

| 모드 | 동작 |
|---|---|
| `dry-run` | 발행하지 않고 미리보기 HTML만 생성 |
| `draft` | Blogger에 초안으로 저장 (공개 안 됨) |
| `publish` | 실제 발행 |

---

## 로컬에서 테스트하기

```bash
pip install -r requirements.txt

export GEMINI_API_KEY="..."
export BLOGGER_CLIENT_ID="..."
export BLOGGER_CLIENT_SECRET="..."
export BLOGGER_REFRESH_TOKEN="..."
export BLOGGER_BLOG_ID="..."

python main.py --dry-run   # 미리보기만
python main.py --draft     # 초안 저장
python main.py             # 실제 발행
```

한글 폰트가 없으면 이미지 글자가 네모로 깨집니다.

```bash
# Ubuntu
sudo apt-get install fonts-noto-cjk fonts-nanum
# macOS는 기본 한글 폰트가 있어 대개 그대로 동작합니다
```

---

## 자주 손대게 되는 설정

전부 `config.py` 한 곳에 모여 있습니다.

| 항목 | 위치 | 설명 |
|---|---|---|
| 뉴스 키워드 | `NEWS_KEYWORDS` | 어떤 주제를 수집할지 |
| 브랜드 색상 | `BRAND` | 이미지 색상 톤 |
| Gemini 모델 | `GEMINI_MODEL` | 모델명이 바뀔 때 수정 |
| 발행 시각 | `.github/workflows/post.yml` 의 cron | UTC 기준 |

글의 말투·구조를 바꾸고 싶으면 `scripts/writer.py` 의
`ARTICLE_PROMPT` 를 수정하면 됩니다.

---

## 문제가 생겼을 때

| 증상 | 원인과 해결 |
|---|---|
| 이미지 글자가 네모(□) | 한글 폰트 미설치. 워크플로우의 폰트 설치 단계 확인 |
| `토큰 갱신 실패` | Refresh Token 만료. `get_token.py` 재실행 후 Secret 갱신 |
| `HTTP 429` | Gemini 무료 한도 초과. 자동 재시도하며, 계속되면 발행 간격을 늘리세요 |
| 이미지가 안 보임 | GitHub Pages 미활성화 또는 저장소가 Private |
| `JSON 파싱 실패` | Gemini 응답 형식 문제. 대부분 재실행하면 해결됩니다 |

실행 로그는 `Actions` 탭에서 확인할 수 있습니다.

---

## 운영 참고

- 뉴스 원문을 그대로 옮기지 않고 주제만 참고해 새로 작성합니다.
- 글 하단에 참고 기사 링크와 작성일이 자동으로 붙습니다.
- 최근 200개 주제를 `data/history.json`에 기억해 중복을 피합니다.
- 처음 1~2주는 `draft` 모드로 돌려 글 품질을 확인한 뒤
  `publish`로 전환하는 것을 권합니다.
