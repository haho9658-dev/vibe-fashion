"""
VIBEFASHION - 애플리케이션 진입점 (Entry Point)

이 파일을 실행하여 웹 서버를 가동합니다.
실행 방법:
    python run.py
"""

from app import create_app

# 앱 팩토리 함수를 호출하여 Flask 앱 인스턴스 생성
app = create_app()

if __name__ == "__main__":
    # debug=True: 코드 수정 시 서버 자동 재시작 및 에러 상세 표시 (개발 모드)
    # port=5000: http://localhost:5000 또는 http://127.0.0.1:5000 으로 접속
    print("==================================================")
    print(" VIBEFASHION 패션 쇼핑몰 서버가 시작되었습니다.")
    print(" 브라우저 접속 주소: http://127.0.0.1:5000")
    print("==================================================")
    app.run(debug=True, port=5000)
