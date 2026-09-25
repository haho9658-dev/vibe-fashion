-- ============================================================================
-- VIBE-FASHION 쇼핑몰 초기 데이터 (Seed Data)
-- 설명: Supabase SQL Editor에서 실행하여 카테고리 7개, 샘플 상품 4개,
--      첫 번째 상품의 옵션 9개(색상 3종 x 사이즈 3종)를 등록합니다.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. 카테고리 7개 등록 (상의, 하의, 아우터, 원피스/세트, 액세서리, 가방, 신발)
--    slug 기준 충돌 시 한글 카테고리명과 설명, 순서를 최신으로 갱신합니다.
-- ----------------------------------------------------------------------------
INSERT INTO public.categories (name, slug, description, sort_order)
VALUES
    ('상의', 'top', '티셔츠, 니트, 셔츠, 블라우스 등 트렌디한 상의 컬렉션', 1),
    ('하의', 'bottom', '슬랙스, 데님, 팬츠, 스커트 등 다양한 하의 컬렉션', 2),
    ('아우터', 'outer', '자켓, 코트, 가디건, 블레이저 등 시즌 아우터', 3),
    ('원피스/세트', 'dress', '감각적인 실루엣의 데일리 & 스페셜 원피스 및 셋업', 4),
    ('액세서리', 'acc', '모자, 주얼리, 벨트 등 스타일에 포인트를 더하는 액세서리', 5),
    ('가방', 'bag', '숄더백, 토트백, 크로스백 등 데일리 가방 라인업', 6),
    ('신발', 'shoes', '스니커즈, 로퍼, 더비 슈즈, 부츠 등 프리미엄 슈즈', 7)
ON CONFLICT (slug) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order;

-- ----------------------------------------------------------------------------
-- 2. 샘플 상품 4개 등록 (카테고리 연결 및 picsum.photos 썸네일 적용)
--    - 베이직 크롭 티셔츠 (상의): 정가 29,900원 / 할인가 19,900원
--    - 와이드 데님 팬츠 (하의): 정가 49,900원 / 판매가 39,900원
--    - 오버핏 코튼 자켓 (아우터): 정가 79,900원 / 판매가 59,900원
--    - 플로럴 미디 원피스 (원피스/세트): 정가 59,900원 / 판매가 45,900원
-- ----------------------------------------------------------------------------
INSERT INTO public.products (category_id, name, slug, summary, description, original_price, sale_price, badge, thumbnail_url, is_active)
VALUES
    (
        (SELECT id FROM public.categories WHERE slug = 'top'),
        '베이직 크롭 티셔츠',
        'basic-crop-tshirt',
        '부드러운 코튼 소재와 트렌디한 크롭 실루엣의 데일리 티셔츠',
        '고급 코튼 100% 원단을 사용하여 세탁 후에도 변형이 적으며, 하이웨이스트 하의와 매치하기 최적화된 기장감입니다.',
        29900,
        19900,
        'BEST',
        'https://picsum.photos/seed/vibe_crop_tshirt/600/700',
        true
    ),
    (
        (SELECT id FROM public.categories WHERE slug = 'bottom'),
        '와이드 데님 팬츠',
        'wide-denim-pants',
        '내추럴한 워싱과 편안하고 멋스러운 와이드 핏 데님',
        '다리가 길어 보이는 하이라이즈 패턴과 사계절 착용 가능한 적당한 두께감의 탄탄한 프리미엄 데님 팬츠입니다.',
        49900,
        39900,
        'HOT',
        'https://picsum.photos/seed/vibe_wide_denim/600/700',
        true
    ),
    (
        (SELECT id FROM public.categories WHERE slug = 'outer'),
        '오버핏 코튼 자켓',
        'overfit-cotton-jacket',
        '간절기 필수 아이템, 캐주얼하면서도 시크한 오버사이즈 자켓',
        '여유 있는 실루엣으로 두터운 이너와 레이어드하기 좋으며, 바이오 워싱 가공으로 부드러운 터치감을 선사합니다.',
        79900,
        59900,
        'NEW',
        'https://picsum.photos/seed/vibe_cotton_jacket/600/700',
        true
    ),
    (
        (SELECT id FROM public.categories WHERE slug = 'dress'),
        '플로럴 미디 원피스',
        'floral-midi-dress',
        '살랑이는 실루엣과 감각적인 잔꽃 패턴의 미디 원피스',
        '허리 라인을 슬림하게 잡아주는 밴딩 디테일과 걸을 때마다 자연스럽게 퍼지는 플레어 라인이 매력적입니다.',
        59900,
        45900,
        'SALE',
        'https://picsum.photos/seed/vibe_floral_dress/600/700',
        true
    )
ON CONFLICT (slug) DO UPDATE
SET
    category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    summary = EXCLUDED.summary,
    description = EXCLUDED.description,
    original_price = EXCLUDED.original_price,
    sale_price = EXCLUDED.sale_price,
    badge = EXCLUDED.badge,
    thumbnail_url = EXCLUDED.thumbnail_url,
    is_active = EXCLUDED.is_active,
    updated_at = timezone('utc'::text, now());

-- ----------------------------------------------------------------------------
-- 3. 첫 번째 상품(베이직 크롭 티셔츠) 옵션 9개 등록
--    - 색상: 블랙(Black), 화이트(White), 베이지(Beige)
--    - 사이즈: S, M, L (총 3 x 3 = 9개 조합)
--    - 각 옵션별 재고 50개 기본 부여
-- ----------------------------------------------------------------------------
INSERT INTO public.product_options (product_id, color, size, stock_quantity, extra_price)
SELECT 
    p.id AS product_id,
    c.color,
    s.size,
    50 AS stock_quantity,
    0 AS extra_price
FROM 
    public.products p
CROSS JOIN 
    (VALUES ('블랙'), ('화이트'), ('베이지')) AS c(color)
CROSS JOIN 
    (VALUES ('S'), ('M'), ('L')) AS s(size)
WHERE 
    p.slug = 'basic-crop-tshirt'
ON CONFLICT (product_id, color, size) DO UPDATE
SET
    stock_quantity = EXCLUDED.stock_quantity,
    extra_price = EXCLUDED.extra_price;

-- ----------------------------------------------------------------------------
-- 4. 등록 결과 검증 조회 (실행 시 Results 탭에서 바로 확인 가능)
-- ----------------------------------------------------------------------------
SELECT 
    p.name AS "상품명",
    c.name AS "카테고리",
    p.sale_price AS "판매가",
    p.original_price AS "정가",
    p.badge AS "배지",
    COUNT(opt.id) AS "등록된 옵션수"
FROM public.products p
JOIN public.categories c ON p.category_id = c.id
LEFT JOIN public.product_options opt ON p.id = opt.product_id
WHERE p.slug IN ('basic-crop-tshirt', 'wide-denim-pants', 'overfit-cotton-jacket', 'floral-midi-dress')
GROUP BY p.id, p.name, c.name, p.sale_price, p.original_price, p.badge
ORDER BY p.id;
