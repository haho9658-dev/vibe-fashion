"""
Azure App Service 및 WSGI 서버용 진입점 (app.py)
Gunicorn 기본 설정인 'gunicorn app:app' 명령을 바로 지원합니다.
"""

import sys
from pathlib import Path

# 현재 프로젝트 디렉터리를 sys.path 최상단에 추가하여 모듈 임포트 실패 방지
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
