#!/bin/bash
# Azure Linux App Service 자동 시작 스크립트 (startup.sh)

# 1. 압축 해제된 임시 앱 디렉터리가 있으면 그곳으로, 없으면 wwwroot로 이동
if [ -d "$APP_PATH" ]; then
    TARGET_DIR="$APP_PATH"
elif [ -d "/home/site/wwwroot" ]; then
    TARGET_DIR="/home/site/wwwroot"
else
    TARGET_DIR="$(pwd)"
fi

cd "$TARGET_DIR"

# 2. PYTHONPATH에 현재 소스 디렉터리와 가상환경 site-packages 추가
export PYTHONPATH="$TARGET_DIR:$TARGET_DIR/antenv/lib/python3.13/site-packages:$PYTHONPATH"

# 3. 가상환경 activate (존재할 경우)
if [ -f "$TARGET_DIR/antenv/bin/activate" ]; then
    source "$TARGET_DIR/antenv/bin/activate"
elif [ -f "/home/site/wwwroot/antenv/bin/activate" ]; then
    source "/home/site/wwwroot/antenv/bin/activate"
fi

# 4. Gunicorn 실행
echo "=== Starting VIBEFASHION with Gunicorn in $TARGET_DIR ==="
exec gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout=120 "wsgi:app"
