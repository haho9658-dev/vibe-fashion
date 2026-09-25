"""
인증 라우트(Blueprint) 모듈
- 로그인, 회원가입, 로그아웃 기능을 담당합니다.
- supabase-py 클라이언트를 활용하여 안전하게 계정 인증을 수행합니다.
- 코딩 규칙 준수: 한국어 주석, 한국어 에러 메시지 표시
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.supabase_client import get_supabase_client

# 'auth' 블루프린트 생성 (URL 접두사: /auth)
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    로그인 처리 뷰 함수
    - GET: 로그인 폼 화면 표시
    - POST: 이메일과 비밀번호를 검증하여 로그인 처리
    """
    # 이미 로그인된 상태라면 메인 페이지로 이동
    if "user" in session:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # 1. 필수 입력값 검증
        if not email or not password:
            flash("이메일과 비밀번호를 모두 입력해주세요.", "danger")
            return render_template("auth/login.html", email=email)

        supabase = get_supabase_client()

        # 2-A. 실제 Supabase 연동 모드
        if supabase:
            try:
                # supabase-py의 auth API를 사용하여 로그인 시도
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                if response.user:
                    # 세션에 사용자 정보 저장
                    session["user"] = {
                        "id": response.user.id,
                        "email": response.user.email,
                        "name": response.user.user_metadata.get("name", email.split("@")[0])
                    }
                    flash(f"환영합니다, {session['user']['name']}님!", "success")
                    return redirect(url_for("main.index"))
                else:
                    flash("로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.", "danger")
            except Exception as e:
                # 한국어 에러 메시지 처리
                error_msg = str(e)
                if "Invalid login credentials" in error_msg:
                    flash("아이디 또는 비밀번호가 일치하지 않습니다.", "danger")
                elif "Email not confirmed" in error_msg:
                    flash("이메일 인증이 완료되지 않았습니다. 메일함을 확인해주세요.", "warning")
                else:
                    flash(f"로그인 중 오류가 발생했습니다: {error_msg}", "danger")

        # 2-B. 개발/로컬 데모 모드 (Supabase 키 미설정 시)
        else:
            # 초보자 및 개발자가 즉시 체험할 수 있도록 제공되는 데모 로그인 처리
            session["user"] = {
                "id": "demo-user-id-001",
                "email": email,
                "name": email.split("@")[0]
            }
            flash(
                "체험 모드로 로그인되었습니다. (실제 운영 시에는 .env에 Supabase 키를 등록하세요)",
                "success"
            )
            return redirect(url_for("main.index"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    회원가입 처리 뷰 함수
    - GET: 회원가입 폼 화면 표시
    - POST: 신규 회원 등록 처리
    """
    if "user" in session:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        name = request.form.get("name", "").strip()

        # 1. 유효성 검사
        if not email or not password:
            flash("이메일과 비밀번호를 모두 입력해주세요.", "danger")
            return render_template("auth/register.html", email=email, name=name)

        if password != password_confirm:
            flash("비밀번호와 비밀번호 확인이 일치하지 않습니다.", "danger")
            return render_template("auth/register.html", email=email, name=name)

        if len(password) < 6:
            flash("비밀번호는 최소 6자 이상이어야 합니다.", "danger")
            return render_template("auth/register.html", email=email, name=name)

        supabase = get_supabase_client()

        # 2-A. 실제 Supabase 연동 모드
        if supabase:
            try:
                # supabase-py를 통한 신규 사용자 등록
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "name": name or email.split("@")[0]
                        }
                    }
                })

                if response.user:
                    flash("회원가입이 완료되었습니다! 로그인해주세요.", "success")
                    return redirect(url_for("auth.login"))
                else:
                    flash("회원가입 처리에 실패했습니다. 다시 시도해주세요.", "danger")
            except Exception as e:
                error_msg = str(e)
                if "User already registered" in error_msg:
                    flash("이미 등록된 이메일 주소입니다.", "warning")
                else:
                    flash(f"회원가입 중 오류가 발생했습니다: {error_msg}", "danger")

        # 2-B. 데모 모드
        else:
            flash("회원가입이 완료되었습니다! (데모 모드) 바로 로그인해보세요.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    """
    로그아웃 처리 뷰 함수
    - 세션 정보 제거 및 Supabase 로그아웃 호출
    """
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

    session.clear()
    flash("정상적으로 로그아웃되었습니다.", "info")
    return redirect(url_for("main.index"))
