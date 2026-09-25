"""
VIBEFASHION - 애플리케이션 팩토리 모듈
이 모듈은 Flask 앱 인스턴스를 생성하고 초기화하는 역할을 담당합니다.
앱 팩토리 패턴(create_app)을 사용하여 설정 변경 및 테스트가 쉬운 구조를 만듭니다.
"""

import os
from flask import Flask
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기
load_dotenv()


def create_app():
    """
    Flask 애플리케이션 팩토리 함수
    - Flask 앱 인스턴스 생성
    - 시크릿 키 등 기본 설정 적용
    - 라우트(블루프린트) 등록
    """
    # 1. Flask 애플리케이션 생성
    app = Flask(__name__)

    # 2. 기본 보안 설정 (세션 및 CSRF 방지 등에 사용)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default-dev-secret-key")

    # 3. 블루프린트(라우트 분리 모듈) 등록
    from app.routes.main import main_bp
    from app.routes.auth_routes import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app
