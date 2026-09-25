-- ============================================================================
-- VIBE-FASHION 쇼핑몰 데이터베이스 스키마
-- 설명: Supabase SQL Editor에서 전체 복사 후 실행(Run)할 수 있는 통합 DDL 스크립트입니다.
-- 테이블: profiles, categories, products, product_options, product_images,
--        carts, orders, order_items, refunds, notifications, reviews
-- 기능: auth.users 연동 및 자동 프로필 생성 트리거, 고객 등급 자동 계산 함수, RLS 정책 포함
-- ============================================================================

-- 0. 확장 기능 활성화 (UUID 생성 등)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. profiles (회원 프로필 테이블)
--    Supabase 내장 auth.users와 1:1로 연결됩니다.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    nickname TEXT,
    avatar_url TEXT,
    phone TEXT,
    grade TEXT NOT NULL DEFAULT 'BRONZE' CHECK (grade IN ('BRONZE', 'SILVER', 'GOLD', 'VIP')), -- 등급: 브론즈/실버/골드/VIP
    total_spent NUMERIC(12, 2) NOT NULL DEFAULT 0, -- 누적 구매 금액 (등급 산정 기준)
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 2. categories (상품 카테고리 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.categories (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,       -- 카테고리명 (예: OUTER, TOP, BOTTOM, SHOES, ACC)
    slug TEXT NOT NULL UNIQUE,       -- URL용 슬러그 (예: outer, top, bottom)
    description TEXT,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 3. products (상품 마스터 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.products (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT REFERENCES public.categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    slug TEXT UNIQUE,
    summary TEXT,                    -- 한 줄 요약 설명
    description TEXT,                -- 상세 설명 (HTML/Markdown)
    original_price NUMERIC(12, 2) NOT NULL, -- 정가
    sale_price NUMERIC(12, 2) NOT NULL,     -- 판매가 (할인가)
    badge TEXT DEFAULT 'NEW',        -- 배지 (NEW, BEST, HOT, SALE 등)
    thumbnail_url TEXT,              -- 대표 썸네일 이미지
    is_active BOOLEAN NOT NULL DEFAULT true, -- 노출 여부
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 4. product_options (상품 옵션 테이블 - 사이즈/컬러 및 재고 관리)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.product_options (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
    color TEXT NOT NULL,             -- 색상 (예: 블랙, 네이비, 아이보리)
    size TEXT NOT NULL,              -- 사이즈 (예: S, M, L, FREE)
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0), -- 재고 수량
    extra_price NUMERIC(12, 2) NOT NULL DEFAULT 0, -- 추가 금액
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_product_color_size UNIQUE (product_id, color, size)
);

-- ----------------------------------------------------------------------------
-- 5. product_images (상품 추가 갤러리 이미지 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.product_images (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 6. carts (장바구니 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.carts (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    product_option_id BIGINT NOT NULL REFERENCES public.product_options(id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_cart_item UNIQUE (user_id, product_option_id)
);

-- ----------------------------------------------------------------------------
-- 7. orders (주문 마스터 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number TEXT UNIQUE NOT NULL, -- 사용자용 주문번호 (예: ORD-20260926-XXXX)
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    total_amount NUMERIC(12, 2) NOT NULL, -- 총 상품 금액
    shipping_fee NUMERIC(12, 2) NOT NULL DEFAULT 3000, -- 배송비
    final_amount NUMERIC(12, 2) NOT NULL, -- 실 결제 금액
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PAID', 'PREPARING', 'SHIPPING', 'DELIVERED', 'CANCELLED')),
    recipient_name TEXT NOT NULL,
    recipient_phone TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    shipping_memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 8. order_items (주문 상세 항목 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    product_option_id BIGINT REFERENCES public.product_options(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    option_color TEXT NOT NULL,
    option_size TEXT NOT NULL,
    price NUMERIC(12, 2) NOT NULL, -- 구매 당시 단가
    quantity INT NOT NULL CHECK (quantity > 0),
    total_price NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 9. refunds (환불 및 반품 요청 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.refunds (
    id BIGSERIAL PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'REQUESTED' CHECK (status IN ('REQUESTED', 'APPROVED', 'REJECTED', 'COMPLETED')),
    admin_memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 10. notifications (고객 알림 테이블 - 주문/배송/프로모션)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'ORDER' CHECK (type IN ('ORDER', 'SHIPPING', 'EVENT', 'GRADE')),
    is_read BOOLEAN NOT NULL DEFAULT false,
    link_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ----------------------------------------------------------------------------
-- 11. reviews (상품 리뷰 테이블)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reviews (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5), -- 1 ~ 5점 평점
    content TEXT NOT NULL,
    image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ============================================================================
-- 12. 트리거 함수 1: 신규 유저 생성(소셜/이메일) 시 profiles 자동 생성 트리거
-- ============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, name, nickname, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'name',
            split_part(NEW.email, '@', 1)
        ),
        COALESCE(
            NEW.raw_user_meta_data->>'nickname',
            split_part(NEW.email, '@', 1)
        ),
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO UPDATE
    SET
        email = EXCLUDED.email,
        name = COALESCE(EXCLUDED.name, public.profiles.name),
        avatar_url = COALESCE(EXCLUDED.avatar_url, public.profiles.avatar_url),
        updated_at = timezone('utc'::text, now());

    RETURN NEW;
END;
$$;

-- auth.users 테이블에 트리거 부착
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- 13. 함수 및 트리거 2: 고객 누적 결제금액 및 등급 자동 업데이트 함수
--     기준:
--       VIP:    1,000,000원 이상
--       GOLD:     500,000원 이상
--       SILVER:   200,000원 이상
--       BRONZE:   200,000원 미만
-- ============================================================================
CREATE OR REPLACE FUNCTION public.update_customer_grade()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user_id UUID;
    v_total_spent NUMERIC(12, 2);
    v_new_grade TEXT;
BEGIN
    -- 결제 완료(PAID, DELIVERED 등)된 주문을 기준으로 사용자 결정
    v_user_id := NEW.user_id;

    -- 완료된 유효 주문 누적 금액 합산 계산
    SELECT COALESCE(SUM(final_amount), 0)
    INTO v_total_spent
    FROM public.orders
    WHERE user_id = v_user_id
      AND status IN ('PAID', 'PREPARING', 'SHIPPING', 'DELIVERED');

    -- 등급 판정
    IF v_total_spent >= 1000000 THEN
        v_new_grade := 'VIP';
    ELSIF v_total_spent >= 500000 THEN
        v_new_grade := 'GOLD';
    ELSIF v_total_spent >= 200000 THEN
        v_new_grade := 'SILVER';
    ELSE
        v_new_grade := 'BRONZE';
    END IF;

    -- 회원 프로필 갱신
    UPDATE public.profiles
    SET total_spent = v_total_spent,
        grade = v_new_grade,
        updated_at = timezone('utc'::text, now())
    WHERE id = v_user_id;

    RETURN NEW;
END;
$$;

-- orders 상태가 결제 완료 및 변경될 때 자동 호출 트리거 부착
DROP TRIGGER IF EXISTS on_order_status_grade_update ON public.orders;
CREATE TRIGGER on_order_status_grade_update
    AFTER INSERT OR UPDATE OF status, final_amount ON public.orders
    FOR EACH ROW
    EXECUTE FUNCTION public.update_customer_grade();

-- ============================================================================
-- 14. 행 수준 보안 (Row Level Security - RLS) 기본 정책 활성화
-- ============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.carts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.refunds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- 조회 정책: 상품 및 카테고리, 리뷰 등은 누구나 조회 가능
CREATE POLICY "카테고리 누구나 조회" ON public.categories FOR SELECT USING (true);
CREATE POLICY "상품 누구나 조회" ON public.products FOR SELECT USING (is_active = true);
CREATE POLICY "상품옵션 누구나 조회" ON public.product_options FOR SELECT USING (true);
CREATE POLICY "상품이미지 누구나 조회" ON public.product_images FOR SELECT USING (true);
CREATE POLICY "리뷰 누구나 조회" ON public.reviews FOR SELECT USING (true);

-- 개인정보 및 구매 정책: 본인 데이터만 접근 가능
CREATE POLICY "프로필 본인 조회" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "프로필 본인 수정" ON public.profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "장바구니 본인 전체 제어" ON public.carts FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "주문 본인 조회" ON public.orders FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "주문 생성 본인 가능" ON public.orders FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "주문상세 본인 조회" ON public.order_items FOR SELECT
    USING (EXISTS (SELECT 1 FROM public.orders WHERE orders.id = order_items.order_id AND orders.user_id = auth.uid()));

CREATE POLICY "알림 본인 조회 및 수정" ON public.notifications FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "환불 본인 조회 및 생성" ON public.refunds FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "리뷰 본인 작성 및 수정" ON public.reviews FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- 15. 초기 카테고리 및 샘플 상품 데이터 (선택 사항)
-- ============================================================================
INSERT INTO public.categories (name, slug, sort_order)
VALUES 
    ('OUTER', 'outer', 1),
    ('TOP', 'top', 2),
    ('BOTTOM', 'bottom', 3),
    ('SHOES', 'shoes', 4),
    ('ACC', 'acc', 5)
ON CONFLICT (slug) DO UPDATE
SET name = EXCLUDED.name, sort_order = EXCLUDED.sort_order;

INSERT INTO public.products (category_id, name, slug, summary, description, original_price, sale_price, badge, thumbnail_url)
VALUES 
    (1, '오버핏 미니멀 블레이저', 'overfit-minimal-blazer', '트렌디한 실루엣의 모던 블레이저', '어떤 이너와도 잘 어울리는 트렌디하고 편안한 실루엣의 블레이저입니다.', 159000, 129000, 'BEST', 'https://picsum.photos/seed/vibe_blazer/600/700'),
    (3, '와이드 투턱 슬랙스', 'wide-two-tuck-slacks', '자연스러운 드레이프감의 슬랙스', '자연스러운 드레이프감과 편안한 착용감을 선사하는 와이드 팬츠입니다.', 85000, 68000, 'NEW', 'https://picsum.photos/seed/vibe_slacks/600/700'),
    (2, '프리미엄 캐시미어 니트', 'premium-cashmere-knit', '부드러운 터치감의 데일리 니트', '부드러운 터치감과 뛰어난 보온성을 지닌 데일리 프리미엄 니트웨어입니다.', 119000, 89000, 'HOT', 'https://picsum.photos/seed/vibe_knit/600/700'),
    (4, '클래식 레더 더비 슈즈', 'classic-leather-derby', '천연 소가죽 클래식 슈즈', '포멀과 캐주얼을 아우르는 고급스러운 천연 가죽 소재의 더비 슈즈입니다.', 189000, 145000, 'SALE', 'https://picsum.photos/seed/vibe_derby/600/700')
ON CONFLICT (slug) DO NOTHING;
