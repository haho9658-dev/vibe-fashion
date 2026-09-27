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


@main_bp.route("/")
def index():
    """
    메인 페이지 뷰 함수
    - Supabase products 테이블에서 is_active=true, is_featured=true 조건으로 최대 4개 조회
    - 가격 포맷: {:,} 포맷을 적용하여 '19,900원' 형태로 전달
    - 에러 발생 시 빈 리스트로 대체하고 터미널에 에러 로그 출력
    """
    products = []

    try:
        # 1차 시도: is_active=true, is_featured=true 최대 4개 조회
        try:
            response = (
                supabase.table("products")
                .select("id, name, sale_price, original_price, thumbnail_url, badge, summary, description, is_active, is_featured")
                .eq("is_active", True)
                .eq("is_featured", True)
                .limit(4)
                .execute()
            )
            raw_products = response.data or []
        except Exception as query_err:
            # is_featured 컬럼이 아직 없을 경우 is_active=True 상품으로 대체 조회
            if "is_featured" in str(query_err):
                print("[Supabase 안내] 'is_featured' 컬럼이 없어 is_active=True 상품으로 대체 조회합니다.")
                response = (
                    supabase.table("products")
                    .select("id, name, sale_price, original_price, thumbnail_url, badge, summary, description, is_active")
                    .eq("is_active", True)
                    .limit(4)
                    .execute()
                )
                raw_products = response.data or []
            else:
                raise query_err

        # 가격 포맷 가공: {:,}을 사용하여 '19,900원' 형태 구성
        for item in raw_products:
            raw_price = item.get("sale_price") or item.get("original_price") or 0
            try:
                num_price = int(float(raw_price))
                formatted_price = f"{num_price:,}원"
            except (ValueError, TypeError):
                formatted_price = f"{raw_price}원"

            img_url = item.get("thumbnail_url") or item.get("image_url") or "https://picsum.photos/600/700"

            products.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "price": formatted_price,                     # '19,900원' 형태
                "formatted_price": formatted_price,
                "thumbnail_url": img_url,
                "badge": item.get("badge"),
                "summary": item.get("summary", ""),
                "description": item.get("description", item.get("summary", "")),
            })

    except Exception as e:
        # Supabase 연결 실패 또는 쿼리 오류 시 빈 리스트로 대체 & 터미널 로그 출력
        print(f"[Supabase 상품 조회 실패] 오류 내용: {e}")
        traceback.print_exc()
        products = []

    return render_template("index.html", products=products)

