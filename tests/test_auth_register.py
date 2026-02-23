# 단위 테스트 – 회원가입 기능 (User 모델, auth.register 라우트)

import pytest

from app import db
from app.models import User


# ===========================================================================
# 1. User 모델 – set_password, check_password
# ===========================================================================


def test_user_set_password_hashes_password(app_ctx):
    """set_password: 비밀번호가 해싱되어 password_hash에 저장됨."""
    user = User(username="pw_user", email="pw@example.com", password_hash="dummy")
    user.set_password("mySecret123")

    assert user.password_hash != "mySecret123"
    assert user.password_hash.startswith("scrypt:")  # werkzeug 기본 해시 방식


def test_user_check_password_correct(app_ctx):
    """check_password: 올바른 비밀번호 → True."""
    user = User(username="check_user", email="check@example.com", password_hash="")
    user.set_password("correctPw")

    assert user.check_password("correctPw") is True


def test_user_check_password_wrong(app_ctx):
    """check_password: 잘못된 비밀번호 → False."""
    user = User(username="wrong_user", email="wrong@example.com", password_hash="")
    user.set_password("correctPw")

    assert user.check_password("wrongPw") is False


# ===========================================================================
# 2. 회원가입 라우트 – GET /auth/register
# ===========================================================================


def test_register_get_returns_form(client, app_ctx):
    """GET /auth/register → 200, 회원가입 폼 렌더."""
    resp = client.get("/auth/register")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "회원가입" in text
    assert "username" in text
    assert "email" in text
    assert "password" in text


# ===========================================================================
# 3. 회원가입 라우트 – POST 검증 (실패 케이스)
# ===========================================================================


def test_register_post_password_mismatch(client, app_ctx):
    """비밀번호와 비밀번호 확인 불일치 → 400, 에러 메시지."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "pass123",
            "password_confirm": "different",
            "nickname": "",
        },
    )
    assert resp.status_code == 400
    assert "비밀번호와 비밀번호 확인이 일치하지 않습니다" in resp.get_data(as_text=True)


def test_register_post_missing_username(client, app_ctx):
    """사용자명 누락 → 400, 에러 메시지."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "",
            "email": "new@example.com",
            "password": "pass123",
            "password_confirm": "pass123",
            "nickname": "",
        },
    )
    assert resp.status_code == 400
    assert "사용자명, 이메일, 비밀번호는 필수" in resp.get_data(as_text=True)


def test_register_post_missing_email(client, app_ctx):
    """이메일 누락 → 400, 에러 메시지."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "",
            "password": "pass123",
            "password_confirm": "pass123",
            "nickname": "",
        },
    )
    assert resp.status_code == 400
    assert "사용자명, 이메일, 비밀번호는 필수" in resp.get_data(as_text=True)


def test_register_post_missing_password(client, app_ctx):
    """비밀번호 누락 → 400, 에러 메시지."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "",
            "password_confirm": "",
            "nickname": "",
        },
    )
    assert resp.status_code == 400
    assert "사용자명, 이메일, 비밀번호는 필수" in resp.get_data(as_text=True)


def test_register_post_duplicate_username(client, app_ctx):
    """중복 사용자명 → 400, 에러 메시지. (default는 create_app 시 생성됨)"""
    resp = client.post(
        "/auth/register",
        data={
            "username": "default",
            "email": "another@example.com",
            "password": "pass123",
            "password_confirm": "pass123",
            "nickname": "",
        },
    )
    assert resp.status_code == 400
    assert "이미 사용 중인 사용자명" in resp.get_data(as_text=True)


def test_register_post_duplicate_email(client, app_ctx):
    """중복 이메일 → 400, 에러 메시지."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "another_user",
            "email": "default@example.com",
            "password": "pass123",
            "password_confirm": "pass123",
            "nickname": "",
        },
    )
    assert resp.status_code == 400
    assert "이미 사용 중인 이메일" in resp.get_data(as_text=True)


# ===========================================================================
# 4. 회원가입 라우트 – POST 성공 (저장 + 자동 로그인)
# ===========================================================================


def test_register_post_success_creates_user(client, app_ctx):
    """회원가입 성공 → User 생성, 비밀번호 해싱 저장."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "success_user",
            "email": "success@example.com",
            "password": "securePass456",
            "password_confirm": "securePass456",
            "nickname": "닉네임",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302

    user = User.query.filter_by(username="success_user").first()
    assert user is not None
    assert user.email == "success@example.com"
    assert user.nickname == "닉네임"
    assert user.password_hash != "securePass456"
    assert user.check_password("securePass456") is True


def test_register_post_success_redirects_to_home(client, app_ctx):
    """회원가입 성공 → main.index로 리다이렉트."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "redirect_user",
            "email": "redirect@example.com",
            "password": "pass123",
            "password_confirm": "pass123",
            "nickname": "",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/" in resp.location or resp.location.endswith("/")


def test_register_post_success_auto_login(client, app_ctx):
    """회원가입 성공 시 login_user() 호출 → 로그인 상태로 홈 접근."""
    resp = client.post(
        "/auth/register",
        data={
            "username": "login_user",
            "email": "login@example.com",
            "password": "pass123",
            "password_confirm": "pass123",
            "nickname": "",
        },
        follow_redirects=True,
    )
    # 리다이렉트 후 홈 페이지 로드 성공
    assert resp.status_code == 200
    # flash 메시지 확인
    assert "회원가입이 완료되었습니다" in resp.get_data(as_text=True)
