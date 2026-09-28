"""
인증 라우트(Blueprint) 모듈 (호환성 유지용)
- 핵심 인증 구현은 app/routes/auth.py 모듈에 구현되어 있습니다.
"""

from app.routes.auth import auth_bp, login_required, get_auth_alerts, AUTH_MESSAGES

__all__ = ["auth_bp", "login_required", "get_auth_alerts", "AUTH_MESSAGES"]

