"""
Gemini API 호출 래퍼.
무료 티어는 분당 요청 제한이 있으므로 재시도 + 대기 로직을 넣었다.
"""
import json
import re
import time

import requests

import config


class GeminiError(Exception):
    pass


def call(prompt: str, temperature: float = 0.9, max_retries: int = 4) -> str:
    """Gemini에 프롬프트를 보내고 텍스트 응답을 받는다."""
    if not config.GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY가 설정되지 않았습니다.")

    url = config.GEMINI_ENDPOINT.format(model=config.GEMINI_MODEL)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 8192,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": config.GEMINI_API_KEY,
    }

    wait = 8
    last_error = ""

    for attempt in range(1, max_retries + 1):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=120)
        except requests.RequestException as e:
            last_error = f"네트워크 오류: {e}"
            print(f"    재시도 {attempt}/{max_retries} — {last_error}")
            time.sleep(wait)
            wait *= 2
            continue

        if res.status_code == 200:
            data = res.json()
            try:
                parts = data["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts).strip()
            except (KeyError, IndexError):
                raise GeminiError(f"예상과 다른 응답 형식: {json.dumps(data)[:400]}")

        # 429 = 요청 한도 초과, 5xx = 일시적 서버 문제 → 재시도
        if res.status_code == 429 or res.status_code >= 500:
            last_error = f"HTTP {res.status_code}"
            print(f"    재시도 {attempt}/{max_retries} — {last_error} ({wait}초 대기)")
            time.sleep(wait)
            wait *= 2
            continue

        # 그 외는 재시도해도 소용 없음
        raise GeminiError(f"HTTP {res.status_code}: {res.text[:400]}")

    raise GeminiError(f"{max_retries}회 재시도 후 실패 — {last_error}")


def call_json(prompt: str, temperature: float = 0.8):
    """JSON 응답을 기대하는 호출. 코드펜스를 벗겨내고 파싱한다."""
    raw = call(prompt, temperature=temperature)
    text = raw.strip()

    # ```json ... ``` 형태 제거
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 본문 속 첫 JSON 블록만 추출 시도
        match = re.search(r"[\{\[].*[\}\]]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise GeminiError(f"JSON 파싱 실패:\n{raw[:600]}")
