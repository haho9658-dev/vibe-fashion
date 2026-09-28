"""
인증 라우트(Blueprint) 모듈
- 이메일 회원가입, 로그인, 이메일 인증, 비밀번호 찾기 및 재설정 기능을 담당합니다.
- supabase-py 클라이언트를 활용하여 안전하게 계정 인증을 수행합니다.
- 코딩 규칙 준수:
  - 한국어 주석 사용
  - 에러/성공 메시지는 URL 파라미터로 전달하고 한국어로 표시
  - Bootstrap 5 폼 및 alert 컴포넌트 적용
  - 환경변수는 os.getenv()로 읽기
  - login_required 데코레이터 제공 (Flask session의 user_id 확인)
"""

import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session
from app.services.supabase_client import get_supabase_client

# 'auth' 블루프린트 생성 (URL 접두사: /auth)
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# 한국어 알림 메시지 매핑 사전
AUTH_MESSAGES = {
    # 에러 메시지
    "email_not_confirmed": "이메일 인증이 완료되지 않았습니다. 메일함에서 인증 링크를 확인해주세요.",
    "invalid_credentials": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "user_already_registered": "이미 가입된 이메일 주소입니다. 로그인해주세요.",
    "password_mismatch": "비밀번호와 비밀번호 확인이 일치하지 않습니다.",
    "password_too_short": "비밀번호는 최소 6자 이상이어야 합니다.",
    "invalid_token": "인증 토큰이 유효하지 않거나 만료되었습니다. 다시 시도해주세요.",
    "verification_failed": "이메일 인증에 실패했습니다. 유효하지 않거나 만료된 링크입니다.",
    "login_required": "로그인이 필요한 서비스입니다.",
    "missing_fields": "필수 입력 항목을 모두 입력해주세요.",
    "reset_failed": "비밀번호 재설정에 실패했습니다. 다시 시도해주세요.",
    "supabase_error": "인증 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
    # 성공 메시지
    "signup_complete": "회원가입이 완료되었습니다! 전송된 인증 메일을 확인해주세요.",
    "email_verified": "이메일 인증이 성공적으로 완료되었습니다.",
    "reset_email_sent": "비밀번호 재설정 링크가 이메일로 발송되었습니다. 메일함을 확인해주세요.",
    "password_reset_success": "비밀번호가 성공적으로 변경되었습니다. 새 비밀번호로 로그인해주세요.",
    "logged_out": "정상적으로 로그아웃되었습니다."
}


def get_auth_alerts():
    """
    URL 쿼리 파라미터(?error=..., ?message=...)를 읽어
    Bootstrap alert에 표시할 한국어 메시지와 alert 타입을 반환합니다.
    """
    error_key = request.args.get("error", "").strip()
    msg_key = request.args.get("message", "").strip()

    alert_type = None
    alert_msg = None

    if error_key:
        alert_type = "warning" if error_key == "email_not_confirmed" else "danger"
        alert_msg = AUTH_MESSAGES.get(error_key, error_key)
    elif msg_key:
        alert_type = "success"
        alert_msg = AUTH_MESSAGES.get(msg_key, msg_key)

    return alert_type, alert_msg


def login_required(f):
    """
    로그인 필수 접근 제한 데코레이터
    - Flask session에서 user_id 존재 여부를 확인합니다.
    - 미로그인 시 error=login_required 파라미터와 함께 로그인 페이지로 리다이렉트합니다.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", error="login_required", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# [1] GET/POST /auth/login - 로그인 폼 + 처리
# ==============================================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    로그인 처리 뷰 함수
    - GET: 로그인 폼 표시 및 에러/안내 메시지 alert 렌더링
    - POST: Supabase sign_in_with_password 처리
      이메일 미인증 시 error=email_not_confirmed 파라미터로 리다이렉트
    """
    # 이미 로그인된 상태라면 메인 화면으로 이동
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        next_url = request.form.get("next") or request.args.get("next")

        # 1. 필수 입력값 검증
        if not email or not password:
            return redirect(url_for("auth.login", error="missing_fields", email=email, next=next_url))

        supabase = get_supabase_client()

        # 2-A. 실제 Supabase 연동 모드
        if supabase:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                if response and response.user:
                    # Flask 세션에 로그인 사용자 정보 저장
                    session["user_id"] = response.user.id
                    session["user"] = {
                        "id": response.user.id,
                        "email": response.user.email,
                        "name": (response.user.user_metadata or {}).get("name", email.split("@")[0])
                    }
                    if response.session:
                        session["access_token"] = response.session.access_token
                        session["refresh_token"] = response.session.refresh_token

                    # 안전한 내부 URL 검증 후 이동
                    if next_url and next_url.startswith("/"):
                        return redirect(next_url)
                    return redirect(url_for("main.index"))
                else:
                    return redirect(url_for("auth.login", error="invalid_credentials", email=email, next=next_url))

            except Exception as e:
                err_msg = str(e).lower()
                # 이메일 미인증 처리 (요구사항: error=email_not_confirmed)
                if "email not confirmed" in err_msg or "email_not_confirmed" in err_msg:
                    return redirect(url_for("auth.login", error="email_not_confirmed", email=email, next=next_url))
                elif "invalid login credentials" in err_msg or "invalid_credentials" in err_msg:
                    return redirect(url_for("auth.login", error="invalid_credentials", email=email, next=next_url))
                else:
                    return redirect(url_for("auth.login", error="invalid_credentials", email=email, next=next_url))

        # 2-B. 개발/로컬 데모 모드 (Supabase 키 미설정 시)
        else:
            session["user_id"] = "demo-user-id-001"
            session["user"] = {
                "id": "demo-user-id-001",
                "email": email,
                "name": email.split("@")[0]
            }
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("main.index"))

    # GET 요청: URL 파라미터 메시지 추출
    alert_type, alert_msg = get_auth_alerts()
    email = request.args.get("email", "")
    next_url = request.args.get("next", "")

    return render_template(
        "auth/login.html",
        alert_type=alert_type,
        alert_msg=alert_msg,
        email=email,
        next=next_url
    )


# ==============================================================================
# [2] GET/POST /auth/signup - 회원가입 폼 + 처리
# ==============================================================================
@auth_bp.route("/signup", methods=["GET", "POST"])
@auth_bp.route("/register", methods=["GET", "POST"])
def signup():
    """
    회원가입 처리 뷰 함수
    - GET: 회원가입 폼 화면 표시
    - POST: Supabase sign_up 처리 후 가입 성공 시 /auth/signup-complete 페이지 이동
    """
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        name = request.form.get("name", "").strip()

        # 1. 유효성 검사
        if not email or not password:
            return redirect(url_for("auth.signup", error="missing_fields", email=email, name=name))

        if password != password_confirm:
            return redirect(url_for("auth.signup", error="password_mismatch", email=email, name=name))

        if len(password) < 6:
            return redirect(url_for("auth.signup", error="password_too_short", email=email, name=name))

        supabase = get_supabase_client()
        site_url = os.getenv("SITE_URL", "http://localhost:5000").rstrip("/")

        # 2-A. 실제 Supabase 연동 모드
        if supabase:
            try:
                # supabase-py sign_up 호출 (이메일 인증 링크 리다이렉트 URL 지정)
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "email_redirect_to": f"{site_url}/auth/confirm",
                        "data": {
                            "name": name or email.split("@")[0]
                        }
                    }
                })

                if response and response.user:
                    # 가입 성공 시 /auth/signup-complete 페이지 이동
                    return redirect(url_for("auth.signup_complete", email=email))
                else:
                    return redirect(url_for("auth.signup", error="supabase_error", email=email, name=name))

            except Exception as e:
                err_msg = str(e).lower()
                if "already registered" in err_msg or "already exists" in err_msg:
                    return redirect(url_for("auth.signup", error="user_already_registered", email=email, name=name))
                return redirect(url_for("auth.signup", error="supabase_error", email=email, name=name))

        # 2-B. 데모 모드
        else:
            return redirect(url_for("auth.signup_complete", email=email))

    alert_type, alert_msg = get_auth_alerts()
    email = request.args.get("email", "")
    name = request.args.get("name", "")

    return render_template(
        "auth/signup.html",
        alert_type=alert_type,
        alert_msg=alert_msg,
        email=email,
        name=name
    )


# ==============================================================================
# [3] GET /auth/signup-complete - "인증 메일을 보냈습니다" 안내
# ==============================================================================
@auth_bp.route("/signup-complete")
def signup_complete():
    """
    회원가입 완료 안내 페이지
    - 사용자의 이메일 주소로 전송된 인증 메일 확인을 안내합니다.
    """
    email = request.args.get("email", "")
    return render_template("auth/signup_complete.html", email=email)


# ==============================================================================
# [4] GET /auth/confirm - 이메일 인증 링크 클릭 처리
# ==============================================================================
@auth_bp.route("/confirm")
def confirm():
    """
    이메일 인증 링크 처리 뷰 함수
    - verify_otp 호출 → 성공 시 Flask session 저장 → /mypage 이동
    - 쿼리 파라미터 (token_hash, token, code 등) 지원
    """
    token_hash = request.args.get("token_hash", "").strip()
    token = request.args.get("token", "").strip()
    code = request.args.get("code", "").strip()
    otp_type = request.args.get("type", "email").strip()
    email = request.args.get("email", "").strip()

    supabase = get_supabase_client()

    # Supabase 클라이언트 미설정 시 데모 세션 부여
    if not supabase:
        session["user_id"] = "demo-verified-user"
        session["user"] = {
            "id": "demo-verified-user",
            "email": email or "user@vibefashion.com",
            "name": "인증회원"
        }
        return redirect("/mypage")

    try:
        auth_response = None

        # 1. token_hash를 이용한 OTP 검증 (Supabase 기본 이메일 인증 방식)
        if token_hash:
            auth_response = supabase.auth.verify_otp({
                "token_hash": token_hash,
                "type": otp_type
            })
        # 2. email + 6자리 토큰/OTP 검증
        elif token and email:
            auth_response = supabase.auth.verify_otp({
                "email": email,
                "token": token,
                "type": otp_type
            })
        # 3. PKCE auth_code 교환 방식
        elif code:
            auth_response = supabase.auth.exchange_code_for_session({
                "auth_code": code
            })

        # 인증 성공 시 세션 저장 후 /mypage 리다이렉트
        if auth_response and auth_response.user:
            session["user_id"] = auth_response.user.id
            session["user"] = {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "name": (auth_response.user.user_metadata or {}).get("name", (auth_response.user.email or "").split("@")[0])
            }
            if auth_response.session:
                session["access_token"] = auth_response.session.access_token
                session["refresh_token"] = auth_response.session.refresh_token

            return redirect("/mypage")
        else:
            return redirect(url_for("auth.login", error="verification_failed"))

    except Exception as e:
        print(f"[이메일 인증 verify_otp 실패] {e}")
        return redirect(url_for("auth.login", error="verification_failed"))


# ==============================================================================
# [5] GET/POST /auth/forgot-password - 비밀번호 재설정 메일 발송
# ==============================================================================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    비밀번호 찾기(재설정 메일 발송) 뷰 함수
    - GET: 비밀번호 찾기 이메일 입력 폼
    - POST: Supabase reset_password_for_email 호출 후 안내 메시지 전달
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            return redirect(url_for("auth.forgot_password", error="missing_fields"))

        supabase = get_supabase_client()
        site_url = os.getenv("SITE_URL", "http://localhost:5000").rstrip("/")

        if supabase:
            try:
                # 비밀번호 재설정 메일 발송 (재설정 완료 후 /auth/reset-password로 이동)
                supabase.auth.reset_password_for_email(
                    email,
                    options={"redirect_to": f"{site_url}/auth/reset-password"}
                )
            except Exception as e:
                print(f"[비밀번호 재설정 요청 오류] {e}")

        # 보안상 이메일 존재 여부와 무관하게 발송 완료 메시지 표시
        return redirect(url_for("auth.forgot_password", message="reset_email_sent"))

    alert_type, alert_msg = get_auth_alerts()
    return render_template("auth/forgot_password.html", alert_type=alert_type, alert_msg=alert_msg)


# ==============================================================================
# [6] GET/POST /auth/reset-password - 새 비밀번호 설정
# ==============================================================================
@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """
    새 비밀번호 설정 뷰 함수
    - GET: 새 비밀번호 입력 폼
    - POST: Supabase update_user를 통한 새 비밀번호 반영
    """
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        token_hash = request.form.get("token_hash", "").strip()
        code = request.form.get("code", "").strip()

        if not password or not password_confirm:
            return redirect(url_for("auth.reset_password", error="missing_fields", token_hash=token_hash, code=code))

        if password != password_confirm:
            return redirect(url_for("auth.reset_password", error="password_mismatch", token_hash=token_hash, code=code))

        if len(password) < 6:
            return redirect(url_for("auth.reset_password", error="password_too_short", token_hash=token_hash, code=code))

        supabase = get_supabase_client()

        if supabase:
            try:
                # 1. 복구용 토큰/코드 검증을 통한 세션 활성화
                if token_hash:
                    supabase.auth.verify_otp({
                        "token_hash": token_hash,
                        "type": "recovery"
                    })
                elif code:
                    supabase.auth.exchange_code_for_session({"auth_code": code})
                elif session.get("access_token") and session.get("refresh_token"):
                    supabase.auth.set_session(session["access_token"], session["refresh_token"])

                # 2. 사용자 비밀번호 갱신
                supabase.auth.update_user({"password": password})

                # 세션 초기화 후 로그인 페이지로 성공 메시지와 함께 이동
                session.clear()
                return redirect(url_for("auth.login", message="password_reset_success"))

            except Exception as e:
                print(f"[비밀번호 갱신 오류] {e}")
                return redirect(url_for("auth.reset_password", error="reset_failed", token_hash=token_hash, code=code))
        else:
            # 데모 모드
            return redirect(url_for("auth.login", message="password_reset_success"))

    # GET 요청: 토큰 또는 코드 파라미터 보존
    token_hash = request.args.get("token_hash", "")
    code = request.args.get("code", "")
    alert_type, alert_msg = get_auth_alerts()

    return render_template(
        "auth/reset_password.html",
        alert_type=alert_type,
        alert_msg=alert_msg,
        token_hash=token_hash,
        code=code
    )


# ==============================================================================
# [기타] 로그아웃 & 마이페이지
# ==============================================================================
@auth_bp.route("/logout")
def logout():
    """
    로그아웃 처리 뷰 함수
    - Supabase 로그아웃 호출 및 Flask session 초기화
    """
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

    session.clear()
    return redirect(url_for("main.index", message="logged_out"))


@auth_bp.route("/mypage")
@login_required
def mypage():
    """
    마이페이지 뷰 함수 (auth 접두사 버전)
    - login_required 데코레이터 적용
    """
    return render_template("auth/mypage.html", user=session.get("user", {}))
