"""
Azure App Service 및 WSGI 서버용 진입점 (app.py)
Gunicorn 기본 설정인 'gunicorn app:app' 명령을 바로 지원합니다.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
