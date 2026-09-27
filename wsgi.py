"""
WSGI 호환 엔트리포인트 (wsgi.py)
Gunicorn, uWSGI 및 Azure App Service에서 바로 로드할 수 있도록
app 패키지를 Python sys.path에 등록하고 create_app() 및 app 인스턴스를 제공합니다.
"""

import sys
from pathlib import Path

# 현재 파일이 위치한 디렉터리를 sys.path 최상단에 추가하여 'app' 모듈 인식 보장
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app

# Gunicorn이 호출할 수 있는 애플리케이션 객체
app = create_app()

if __name__ == "__main__":
    app.run()
