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

# 기본 더미 상품 데이터 (Supabase 연결 실패 시 또는 환경변수 부재 시 폴백용)
DEFAULT_PRODUCTS = [
    {
        "id": 1,
        "name": "오버핏 미니멀 블레이저",
        "price": "129,000원",
        "formatted_price": "129,000원",
        "thumbnail_url": "https://picsum.photos/seed/vibe_blazer/600/700",
        "badge": "BEST",
        "description": "어떤 이너와도 잘 어울리는 트렌디하고 편안한 실루엣의 블레이저입니다."
    },
    {
        "id": 2,
        "name": "와이드 투턱 슬랙스",
        "price": "68,000원",
        "formatted_price": "68,000원",
        "thumbnail_url": "https://picsum.photos/seed/vibe_slacks/600/700",
        "badge": "NEW",
        "description": "자연스러운 드레이프감과 편안한 착용감을 선사하는 와이드 팬츠입니다."
    },
    {
        "id": 3,
        "name": "프리미엄 캐시미어 니트",
        "price": "89,000원",
        "formatted_price": "89,000원",
        "thumbnail_url": "https://picsum.photos/seed/vibe_knit/600/700",
        "badge": "HOT",
        "description": "부드러운 터치감과 뛰어난 보온성을 지닌 데일리 프리미엄 니트웨어입니다."
    },
    {
        "id": 4,
        "name": "클래식 레더 더비 슈즈",
        "price": "145,000원",
        "formatted_price": "145,000원",
        "thumbnail_url": "https://picsum.photos/seed/vibe_derby/600/700",
        "badge": "SALE",
        "description": "포멀과 캐주얼을 아우르는 고급스러운 천연 가죽 소재의 더비 슈즈입니다."
    }
]


def get_supabase_client():
    """
    요청 시점에 환경 변수를 읽어 Supabase 클라이언트를 생성합니다.
    (배포 환경에서 환경 변수가 런타임에 주입되는 경우 대비)
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    if url and key:
        try:
            return create_client(url, key)
        except Exception as e:
            print(f"[Supabase 클라이언트 생성 실패] {e}")
    return None


@main_bp.route("/")
def index():
    """
    메인 페이지 뷰 함수
    - Supabase DB에서 활성화된 상품을 최대 4개 조회
    - Supabase 연결 실패 또는 데이터가 비어 있을 경우 기본 샘플 상품을 표시하여 화면이 비지 않도록 처리
    """
    products = []
    sb = get_supabase_client()

    if sb:
        try:
            # 1. is_active=true 조건으로 상품 조회 (is_featured 필터 포함 시도 후 폴백)
            try:
                response = (
                    sb.table("products")
                    .select("id, name, sale_price, original_price, thumbnail_url, badge, summary, description, is_active, is_featured")
                    .eq("is_active", True)
                    .eq("is_featured", True)
                    .limit(4)
                    .execute()
                )
                raw_products = response.data or []
            except Exception as feat_err:
                # is_featured 컬럼이 없거나 0건일 경우 is_active=True 상품으로 조회
                response = (
                    sb.table("products")
                    .select("id, name, sale_price, original_price, thumbnail_url, badge, summary, description, is_active")
                    .eq("is_active", True)
                    .limit(4)
                    .execute()
                )
                raw_products = response.data or []

            # 2. 조회된 상품 데이터 가공
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
                    "price": formatted_price,
                    "formatted_price": formatted_price,
                    "thumbnail_url": img_url,
                    "badge": item.get("badge"),
                    "summary": item.get("summary", ""),
                    "description": item.get("description", item.get("summary", "")),
                })
        except Exception as e:
            print(f"[Supabase 상품 조회 실패] 오류 내용: {e}")
            traceback.print_exc()

    # Supabase에서 상품을 가져오지 못했거나 목록이 비어 있는 경우 기본 더미 상품 제공
    if not products:
        print("[안내] Supabase 상품 데이터가 없어 기본 추천 상품을 화면에 렌더링합니다.")
        products = DEFAULT_PRODUCTS

    return render_template("index.html", products=products)

