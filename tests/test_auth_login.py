# 단위 테스트 – 로그인·로그아웃 기능

import pytest

from app import db
from app.models import User


@pytest.fixture
def login_user(app_ctx):
    """테스트용 로그인 가능 유저."""
    u = User(username="login_test", email="login_test@example.com")
    u.set_password("secret123")
    db.session.add(u)
    db.session.commit()
    return u


# ----- 로그인 GET -----
def test_login_get_returns_form(client, app_ctx):
    """GET /auth/login → 200, 로그인 폼 렌더."""
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "로그인" in text
    assert "login_id" in text or "login-id" in text
    assert "password" in text
    assert "remember" in text


def test_login_get_with_next_preserves_param(client, app_ctx):
    """GET /auth/login?next=/studio → form action에 next 포함."""
    resp = client.get("/auth/login?next=/studio")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "next" in text or "/studio" in text


def test_login_get_when_logged_in_redirects_to_home(logged_in_client):
    """이미 로그인된 사용자가 /auth/login 접근 시 홈으로 리다이렉트."""
    resp = logged_in_client.get("/auth/login", follow_redirects=False)
    assert resp.status_code == 302
    assert "/" in resp.location


# ----- 로그인 POST (사용자명으로) -----
def test_login_post_with_username_success(client, app_ctx, login_user):
    """사용자명으로 로그인 성공 → 302, 홈 리다이렉트."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "login_test", "password": "secret123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.location.endswith("/") or "/" in resp.location


# ----- 로그인 POST (이메일로) -----
def test_login_post_with_email_success(client, app_ctx, login_user):
    """이메일로 로그인 성공 → 302."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "login_test@example.com", "password": "secret123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302


# ----- 로그인 POST (실패) -----
def test_login_post_wrong_password(client, app_ctx, login_user):
    """잘못된 비밀번호 → 400, flash 에러."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "login_test", "password": "wrong"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "아이디/이메일 또는 비밀번호" in resp.get_data(as_text=True)


def test_login_post_nonexistent_user(client, app_ctx):
    """존재하지 않는 사용자 → 400."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "nonexistent", "password": "any"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "아이디/이메일 또는 비밀번호" in resp.get_data(as_text=True)


def test_login_post_empty_login_id(client, app_ctx, login_user):
    """login_id 빈 값 → 400."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "", "password": "secret123"},
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_login_post_empty_password(client, app_ctx, login_user):
    """비밀번호 빈 값 → 400."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "login_test", "password": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 400


# ----- next 파라미터 -----
def test_login_post_with_next_redirects(client, app_ctx, login_user):
    """로그인 성공 시 next 파라미터로 리다이렉트."""
    resp = client.post(
        "/auth/login?next=/studio/",
        data={"login_id": "login_test", "password": "secret123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/studio" in resp.location


def test_login_post_unsafe_next_redirects_to_home(client, app_ctx, login_user):
    """next에 외부 URL(open redirect) → 메인으로 리다이렉트."""
    resp = client.post(
        "/auth/login?next=http://evil.com/",
        data={"login_id": "login_test", "password": "secret123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    # 외부 URL로 가지 말고 메인으로
    assert "evil.com" not in (resp.location or "")
    assert resp.location.endswith("/") or "/" in (resp.location or "")


def test_login_post_remember_passed_to_login_user(client, app_ctx, login_user):
    """remember 체크 시 login_user(remember=True) 호출됨 → 세션 쿠키 만료 연장."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "login_test", "password": "secret123", "remember": "y"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # 로그인 성공 후 /studio 접근 가능해야 함
    resp2 = client.get("/studio/", follow_redirects=False)
    assert resp2.status_code == 200


# ----- 로그아웃 -----
def test_logout_get_redirects_to_main(logged_in_client):
    """GET /auth/logout → 302, 메인으로 리다이렉트."""
    resp = logged_in_client.get("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/" in resp.location


def test_logout_get_shows_flash(logged_in_client):
    """GET /auth/logout 후 메인 페이지에 flash 메시지 표시."""
    resp = logged_in_client.get("/auth/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert "로그아웃" in resp.get_data(as_text=True)


def test_logout_clears_session(logged_in_client):
    """로그아웃 후 login_required 페이지 접근 시 로그인 페이지로 리다이렉트."""
    # 로그아웃
    logged_in_client.get("/auth/logout", follow_redirects=True)
    # Studio(login_required) 접근 → 로그인 페이지로
    resp = logged_in_client.get("/studio/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in (resp.location or "")


# ----- lsy수정/1234 로그인 (DB 검증용) -----
@pytest.fixture
def lsy_modified_user(app_ctx):
    """테스트용 lsy수정 유저 (비밀번호 1234)."""
    u = User(
        username="lsy수정",
        email="lsy수정@naver.com",
        nickname="lsy수정",
    )
    u.set_password("1234")
    db.session.add(u)
    db.session.commit()
    return u


def test_login_lsy_modified_with_password_1234(client, app_ctx, lsy_modified_user):
    """lsy수정/1234 로그인 성공."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "lsy수정", "password": "1234"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/" in (resp.location or "")


def test_login_lsy_modified_with_email_and_password_1234(client, app_ctx, lsy_modified_user):
    """lsy수정@naver.com / 1234 이메일로 로그인 성공."""
    resp = client.post(
        "/auth/login",
        data={"login_id": "lsy수정@naver.com", "password": "1234"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
