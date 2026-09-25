"""
메인 라우트(Blueprint) 모듈
홈페이지 및 쇼핑몰 메인 화면을 보여주는 라우트들을 정의합니다.
Supabase DB와 연동하여 추천 상품 목록을 조회하고 템플릿에 전달합니다.
"""

import os
import traceback
from flask import Blueprint, render_template
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일에서 환경변수 로드
load_dotenv()

# 'main'이라는 이름의 블루프린트 생성
main_bp = Blueprint("main", __name__)

# Supabase 클라이언트 캐싱
_supabase_client: Client | None = None


def get_supabase() -> Client | None:
    """
    .env 환경변수(SUPABASE_URL, SUPABASE_ANON_KEY)를 읽어
    supabase-py 클라이언트를 생성하여 반환합니다.
    연결 실패 또는 키 누락 시 None을 반환하고 터미널에 에러를 출력합니다.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("[Supabase 설정 오류] SUPABASE_URL 또는 SUPABASE_ANON_KEY가 설정되지 않았습니다.")
        return None

    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except Exception as e:
        print(f"[Supabase 클라이언트 생성 실패] {e}")
        traceback.print_exc()
        return None


def fetch_featured_products() -> list:
    """
    Supabase products 테이블에서 상품 데이터를 조회합니다.
    - 조건: is_active=true, is_featured=true (is_featured 컬럼 부재 시 is_active=true로 대체 폴백)
    - 최대 4개 조회
    - 가격 포맷: {:,} 포맷을 적용하여 '19,900원' 형태로 변환
    - 에러 발생 시 빈 리스트([]) 반환 및 터미널에 로그 출력
    """
    supabase = get_supabase()
    if not supabase:
        print("[Supabase 알림] 클라이언트를 초기화할 수 없어 빈 상품 목록을 반환합니다.")
        return []

    try:
        # 1차 시도: is_active=true 및 is_featured=true 조건으로 최대 4개 조회
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
            # is_featured 컬럼이 테이블에 아직 추가되지 않았을 경우의 폴백 처리
            err_str = str(query_err)
            if "is_featured" in err_str:
                print("[Supabase 안내] products 테이블에 'is_featured' 컬럼이 없어 is_active=True 상품으로 대체 조회합니다.")
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

        # 템플릿 표시용 데이터 가공 (가격 포맷 등)
        formatted_products = []
        for item in raw_products:
            # 가격 포맷: {:,}을 사용하여 '19,900원' 형태로 설정
            raw_price = item.get("sale_price") or item.get("original_price") or 0
            try:
                num_price = int(float(raw_price))
                formatted_price = f"{num_price:,}원"
            except (ValueError, TypeError):
                formatted_price = f"{raw_price}원"

            # 썸네일 이미지 URL (thumbnail_url 또는 image_url)
            img_url = item.get("thumbnail_url") or item.get("image_url") or "https://picsum.photos/600/700"

            formatted_products.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "price": formatted_price,                      # 요구사항: '19,900원' 형태
                "formatted_price": formatted_price,
                "thumbnail_url": img_url,                      # 썸네일 이미지 URL
                "badge": item.get("badge"),
                "summary": item.get("summary", ""),
                "description": item.get("description", item.get("summary", "")),
            })

        return formatted_products

    except Exception as e:
        # 연결 실패 또는 쿼리 오류 발생 시 터미널에 에러 로그 출력 후 빈 리스트 반환
        print(f"[Supabase 상품 조회 실패] 오류 내용: {e}")
        traceback.print_exc()
        return []


@main_bp.route("/")
def index():
    """
    쇼핑몰 메인 페이지 뷰 함수
    - Supabase에서 조회한 상품 목록을 products 변수로 index.html 템플릿에 전달합니다.
    """
    products = fetch_featured_products()
    return render_template("index.html", products=products)
