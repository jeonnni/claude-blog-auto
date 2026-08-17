"""
Blogger refresh token 발급기 — 내 PC에서 딱 한 번만 실행하면 된다.

사용법:
    1) pip install google-auth-oauthlib
    2) python get_token.py
    3) 브라우저가 열리면 블로그 만든 구글 계정으로 로그인 → 허용
    4) 터미널에 출력된 refresh token을 복사
    5) GitHub 저장소 Settings → Secrets → Actions 에서
       BLOGGER_REFRESH_TOKEN 이라는 이름으로 등록

주의: 이 스크립트는 GitHub Actions에서 실행되지 않는다. 로컬 전용.
"""
import json
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("먼저 설치가 필요합니다:  pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/blogger"]


def main():
    print("=" * 60)
    print(" Blogger Refresh Token 발급기")
    print("=" * 60)
    print()
    print("Google Cloud Console에서 받은 값을 입력하세요.")
    print("(입력값은 이 컴퓨터 밖으로 나가지 않습니다)")
    print()

    client_id = input("클라이언트 ID: ").strip()
    client_secret = input("클라이언트 보안 비밀: ").strip()

    if not client_id or not client_secret:
        print("\n값이 비어 있습니다. 다시 실행해 주세요.")
        sys.exit(1)

    if not client_id.endswith(".apps.googleusercontent.com"):
        print("\n[경고] 클라이언트 ID가 보통 .apps.googleusercontent.com 으로 끝납니다.")
        if input("그래도 계속할까요? (y/n): ").strip().lower() != "y":
            sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("\n브라우저를 엽니다. 구글 로그인 후 '허용'을 눌러주세요.")
    print("('앱이 확인되지 않았습니다' 화면이 나오면")
    print(" → 고급 → 안전하지 않은 페이지로 이동 을 눌러 진행하면 됩니다)\n")

    # access_type=offline + prompt=consent 를 줘야 refresh_token이 발급된다
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    if not creds.refresh_token:
        print("\n[실패] refresh token이 발급되지 않았습니다.")
        print("이미 승인한 적이 있다면 아래 주소에서 앱 권한을 삭제 후 다시 시도하세요.")
        print("https://myaccount.google.com/permissions")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" 발급 성공! 아래 값을 GitHub Secret에 등록하세요.")
    print("=" * 60)
    print()
    print("  Secret 이름 : BLOGGER_REFRESH_TOKEN")
    print(f"  Secret 값   : {creds.refresh_token}")
    print()
    print("=" * 60)

    # 백업 파일로도 저장
    with open("refresh_token.txt", "w", encoding="utf-8") as f:
        f.write(creds.refresh_token)
    print("\nrefresh_token.txt 파일로도 저장했습니다.")
    print("등록이 끝나면 이 파일은 삭제하세요. (절대 깃허브에 올리지 마세요)")


if __name__ == "__main__":
    main()
