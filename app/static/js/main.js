/**
 * VIBEFASHION 메인 스크립트
 * 초보자도 쉽게 이해할 수 있도록 구성된 장바구니 인터랙션 코드입니다.
 */

document.addEventListener("DOMContentLoaded", function () {
    // 장바구니 개수 상태 변수
    let cartCount = 0;

    // 네비게이션 바의 장바구니 뱃지 요소 선택
    const cartBadge = document.getElementById("cartCountBadge");
    const cartBtn = document.getElementById("cartBtn");

    // '장바구니 담기' 버튼들 선택
    const addToCartButtons = document.querySelectorAll(".add-to-cart-btn");

    // 모든 장바구니 버튼에 클릭 이벤트 리스너 연결
    addToCartButtons.forEach(button => {
        button.addEventListener("click", function () {
            const productName = this.getAttribute("data-product-name");

            // 1. 장바구니 개수 1 증가
            cartCount += 1;
            cartBadge.textContent = cartCount;

            // 2. 부드러운 애니메이션 효과 부여
            cartBadge.classList.add("bg-success");
            cartBadge.classList.remove("bg-danger");

            setTimeout(() => {
                cartBadge.classList.remove("bg-success");
                cartBadge.classList.add("bg-danger");
            }, 500);

            // 3. 사용자 알림 메시지
            alert(`[${productName}] 상품이 장바구니에 담겼습니다!`);
        });
    });

    // 네비게이션 바 장바구니 버튼 클릭 시
    if (cartBtn) {
        cartBtn.addEventListener("click", function () {
            alert(`현재 장바구니에 총 ${cartCount}개의 상품이 담겨 있습니다.`);
        });
    }
});
