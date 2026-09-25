# app/routes/main.py - 메인 페이지 라우트
import os
import traceback
from flask import Blueprint, render_template
from dotenv import load_dotenv
from supabase import create_client

# .env 환경 변수 로드
load_dotenv()

# 'main' 블루프린트 생성
main_bp = Blueprint("main", __name__)

# .env 의 URL·키를 읽어 supabase-py 클라이언트를 만든다
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
)


@main_bp.route('/')
def index():
    try:
        result = supabase.table('products')\
            .select('*')\
            .eq('is_active', True)\
            .eq('is_featured', True)\
            .limit(4).execute()
        products = result.data
    except Exception as e:
        print(f'Supabase 연결 실패: {e}')
        products = []
    return render_template('index.html', products=products)


