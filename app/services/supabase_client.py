"""
Supabase 클라이언트 초기화 모듈
- 코딩 규칙 준수: 환경변수는 반드시 os.getenv()로 읽기 (.env 직접 참조 금지)
- Supabase 클라이언트는 항상 supabase-py 라이브러리를 사용합니다.
"""

import os
from supabase import create_client, Client


def get_supabase_client() -> Client | None:
    """
    Supabase 클라이언트를 생성하여 반환하는 헬퍼 함수
    환경변수 SUPABASE_URL 및 SUPABASE_KEY(또는 SUPABASE_ANON_KEY)를 확인합니다.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    # 유효한 URL과 KEY가 설정되어 있는지 확인 (기본 예시 값이 아닌 실제 값)
    if (
        supabase_url
        and supabase_key
        and not supabase_url.startswith("https://your-project")
        and supabase_key != "your-supabase-anon-key"
    ):
        try:
            return create_client(supabase_url, supabase_key)
        except Exception as e:
            # 클라이언트 생성 실패 시 콘솔에 알림
            print(f"[Supabase 초기화 오류] {e}")
            return None

    return None
