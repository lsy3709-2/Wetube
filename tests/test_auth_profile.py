# 단위 테스트 – 프로필 수정 기능 (lsy/1234 → lsy수정/1234수정)

import os
from io import BytesIO

import pytest
from PIL import Image

from app import db
from app.models import User


@pytest.fixture
def lsy_user(app_ctx):
    """테스트용 lsy 유저 (비밀번호 1234)."""
    u = User(username="lsy", email="lsy@example.com", nickname=None)
    u.set_password("1234")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def profile_user(app_ctx):
    """테스트용 프로필 수정 대상 유저 (기존 호환용)."""
    u = User(username="profile_test", email="profile@example.com", nickname="테스트")
    u.set_password("oldpass")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def logged_in_lsy_client(client, app_ctx, lsy_user):
    """lsy/1234 유저로 로그인된 클라이언트."""
    client.post(
        "/auth/login",
        data={"login_id": "lsy", "password": "1234"},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def logged_in_profile_client(client, app_ctx, profile_user):
    """profile_test 유저로 로그인된 클라이언트."""
    client.post(
        "/auth/login",
        data={"login_id": "profile_test", "password": "oldpass"},
        follow_redirects=True,
    )
    return client


# ----- GET -----
def test_profile_get_returns_form(logged_in_profile_client):
    """GET /auth/profile → 200, 닉네임·이메일 pre-filled."""
    resp = logged_in_profile_client.get("/auth/profile")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "마이페이지" in text or "회원" in text
    assert "nickname" in text and "email" in text
    assert "profile@example.com" in text
    assert "테스트" in text
    assert "current_password" in text
    assert "new_password" in text


def test_profile_get_requires_login(client):
    """미로그인 시 /auth/profile → 302, /auth/login으로 리다이렉트."""
    resp = client.get("/auth/profile", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in (resp.location or "")


# ----- POST: 닉네임·이메일 수정 -----
def test_profile_post_update_nickname_email(logged_in_profile_client, app_ctx, profile_user):
    """닉네임·이메일만 수정 (비밀번호 변경 없음) → 성공."""
    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={
            "nickname": "새닉네임",
            "email": "newemail@example.com",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "회원정보가 수정되었습니다" in resp.get_data(as_text=True)

    db.session.expire_all()
    u = db.session.get(User, profile_user.id)
    assert u.nickname == "새닉네임"
    assert u.email == "newemail@example.com"
    assert u.check_password("oldpass") is True  # 비밀번호 변경 없음


# ----- POST: 이메일 중복 -----
def test_profile_post_duplicate_email_rejected(logged_in_profile_client, app_ctx, profile_user):
    """다른 사용자가 이미 사용 중인 이메일 → 400."""
    other = User(username="other_user", email="other@example.com")
    other.set_password("x")
    db.session.add(other)
    db.session.commit()

    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={"nickname": "테스트", "email": "other@example.com"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "이미 사용 중인 이메일" in resp.get_data(as_text=True)


def test_profile_post_same_email_allowed(logged_in_profile_client, app_ctx, profile_user):
    """본인 이메일 그대로 두기 → 허용."""
    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={"nickname": "변경닉네임", "email": "profile@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "회원정보가 수정되었습니다" in resp.get_data(as_text=True)


# ----- POST: 비밀번호 변경 -----
def test_profile_post_change_password(logged_in_profile_client, app_ctx, profile_user):
    """현재 비밀번호 검증 후 새 비밀번호로 변경."""
    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={
            "nickname": "테스트",
            "email": "profile@example.com",
            "current_password": "oldpass",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    db.session.expire_all()
    u = db.session.get(User, profile_user.id)
    assert u.check_password("newpass123") is True
    assert u.check_password("oldpass") is False


def test_profile_post_wrong_current_password(logged_in_profile_client, app_ctx):
    """현재 비밀번호 틀림 → 400."""
    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={
            "nickname": "테스트",
            "email": "profile@example.com",
            "current_password": "wrong",
            "new_password": "newpass",
            "new_password_confirm": "newpass",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "현재 비밀번호가 올바르지 않습니다" in resp.get_data(as_text=True)


def test_profile_post_new_password_mismatch(logged_in_profile_client, app_ctx):
    """새 비밀번호와 확인 불일치 → 400."""
    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={
            "nickname": "테스트",
            "email": "profile@example.com",
            "current_password": "oldpass",
            "new_password": "newpass",
            "new_password_confirm": "different",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "일치하지 않습니다" in resp.get_data(as_text=True)


def test_profile_post_empty_email_rejected(logged_in_profile_client, app_ctx):
    """이메일 비움 → 400."""
    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={"nickname": "테스트", "email": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "이메일은 필수" in resp.get_data(as_text=True)


def test_profile_post_new_password_too_short(logged_in_profile_client, app_ctx):
    """새 비밀번호 4자 미만 → 400."""
    resp = logged_in_profile_client.post(
        "/auth/profile",
        data={
            "nickname": "테스트",
            "email": "profile@example.com",
            "current_password": "oldpass",
            "new_password": "123",
            "new_password_confirm": "123",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "4자 이상" in resp.get_data(as_text=True)


def test_profile_get_contains_profile_image_input(logged_in_profile_client):
    """GET 응답에 프로필 이미지 업로드 input 및 마이페이지 정보 포함."""
    resp = logged_in_profile_client.get("/auth/profile")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "profile_image" in text
    assert "multipart/form-data" in text or 'enctype="multipart/form-data"' in text
    assert "마이페이지" in text or "프로필" in text


# ----- lsy/1234 → lsy수정/1234수정 시나리오 (문서 검증용) -----
def test_lsy_profile_update_nickname_email_before_after(logged_in_lsy_client, app_ctx, lsy_user):
    """lsy/1234: 닉네임·이메일 수정 전 후 확인. 변경 후 → lsy수정, lsy수정@example.com"""
    # 수정 전
    db.session.expire_all()
    u_before = db.session.get(User, lsy_user.id)
    assert u_before.nickname is None or u_before.nickname == ""
    assert u_before.email == "lsy@example.com"

    # 회원정보 수정 (닉네임 lsy수정, 이메일 lsy수정@example.com)
    resp = logged_in_lsy_client.post(
        "/auth/profile",
        data={
            "nickname": "lsy수정",
            "email": "lsy수정@example.com",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "회원정보가 수정되었습니다" in resp.get_data(as_text=True)

    # 수정 후 DB 확인
    db.session.expire_all()
    u_after = db.session.get(User, lsy_user.id)
    assert u_after.nickname == "lsy수정"
    assert u_after.email == "lsy수정@example.com"
    assert u_after.check_password("1234") is True  # 비밀번호는 아직 1234


def test_lsy_password_change_before_after(logged_in_lsy_client, app_ctx, lsy_user):
    """lsy/1234: 비밀번호 변경 전 후 확인. 1234 → 1234수정"""
    # 수정 전: 1234로 로그인됨
    u = db.session.get(User, lsy_user.id)
    assert u.check_password("1234") is True

    # 비밀번호 변경 (1234 → 1234수정)
    resp = logged_in_lsy_client.post(
        "/auth/profile",
        data={
            "nickname": "",
            "email": "lsy@example.com",
            "current_password": "1234",
            "new_password": "1234수정",
            "new_password_confirm": "1234수정",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # 수정 후: 1234수정만 통과, 1234는 실패
    db.session.expire_all()
    u_after = db.session.get(User, lsy_user.id)
    assert u_after.check_password("1234수정") is True
    assert u_after.check_password("1234") is False


def test_lsy_profile_and_password_full_sequence(logged_in_lsy_client, app_ctx, lsy_user):
    """lsy 전체 시나리오: 1) 회원정보 수정 2) 비밀번호 변경 (순서 안내 검증)"""
    # 1단계: 회원정보 수정 (닉네임·이메일)
    resp1 = logged_in_lsy_client.post(
        "/auth/profile",
        data={"nickname": "lsy수정", "email": "lsy수정@example.com"},
        follow_redirects=True,
    )
    assert resp1.status_code == 200

    db.session.expire_all()
    u = db.session.get(User, lsy_user.id)
    assert u.nickname == "lsy수정"
    assert u.email == "lsy수정@example.com"
    assert u.check_password("1234") is True

    # 2단계: 비밀번호 변경 (1234 → 1234수정)
    resp2 = logged_in_lsy_client.post(
        "/auth/profile",
        data={
            "nickname": "lsy수정",
            "email": "lsy수정@example.com",
            "current_password": "1234",
            "new_password": "1234수정",
            "new_password_confirm": "1234수정",
        },
        follow_redirects=True,
    )
    assert resp2.status_code == 200

    db.session.expire_all()
    u_final = db.session.get(User, lsy_user.id)
    assert u_final.nickname == "lsy수정"
    assert u_final.email == "lsy수정@example.com"
    assert u_final.check_password("1234수정") is True
    assert u_final.check_password("1234") is False


# ----- 프로필 이미지 업로드 -----
def _make_png_bytes():
    """작은 PNG 이미지 바이트 반환."""
    buf = BytesIO()
    img = Image.new("RGB", (20, 20), color="red")
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_profile_post_upload_image_success(logged_in_profile_client, app_ctx, profile_user, app):
    """프로필 이미지 업로드 성공 → DB에 파일명 저장 (로컬 모드)."""
    # Cloudinary env 제거 → 로컬 저장 경로 테스트
    prev = {}
    for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
        prev[key] = os.environ.pop(key, None)
    try:
        png_data = _make_png_bytes()
        data = {
            "nickname": "테스트",
            "email": "profile@example.com",
            "profile_image": (BytesIO(png_data), "avatar.png"),
        }
        resp = logged_in_profile_client.post("/auth/profile", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert "회원정보가 수정되었습니다" in resp.get_data(as_text=True)

        db.session.expire_all()
        u = db.session.get(User, profile_user.id)
        assert u.profile_image is not None
        assert u.profile_image.endswith(".png")
        assert "profile" in u.profile_image or "_" in u.profile_image

        # 실제 파일 저장 확인
        profile_dir = app.config["PROFILE_IMAGE_FOLDER"]
        assert os.path.isfile(os.path.join(profile_dir, u.profile_image))
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v


def test_profile_post_upload_image_invalid_extension_rejected(logged_in_profile_client, app_ctx):
    """허용되지 않는 확장자(bat) 업로드 → 400."""
    data = {
        "nickname": "테스트",
        "email": "profile@example.com",
        "profile_image": (BytesIO(b"fake"), "virus.bat"),
    }
    resp = logged_in_profile_client.post("/auth/profile", data=data, follow_redirects=False)
    assert resp.status_code == 400
    assert "허용" in resp.get_data(as_text=True) or "형식" in resp.get_data(as_text=True)


def test_profile_post_upload_invalid_image_rejected(logged_in_profile_client, app_ctx):
    """이미지가 아닌 파일을 .png로 업로드 → 400."""
    data = {
        "nickname": "테스트",
        "email": "profile@example.com",
        "profile_image": (BytesIO(b"not an image at all"), "fake.png"),
    }
    resp = logged_in_profile_client.post("/auth/profile", data=data, follow_redirects=False)
    assert resp.status_code == 400
    assert "유효하지 않은" in resp.get_data(as_text=True) or "이미지" in resp.get_data(as_text=True)


def test_profile_post_upload_replaces_old_image(logged_in_profile_client, app_ctx, profile_user, app):
    """새 이미지 업로드 시 기존 파일 삭제 후 새 파일 저장 (로컬 모드)."""
    # Cloudinary env 제거 → 로컬 저장 경로 테스트
    prev = {}
    for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
        prev[key] = os.environ.pop(key, None)
    try:
        png_data = _make_png_bytes()
        # 1차 업로드
        data1 = {
            "nickname": "테스트",
            "email": "profile@example.com",
            "profile_image": (BytesIO(png_data), "first.png"),
        }
        resp1 = logged_in_profile_client.post("/auth/profile", data=data1, follow_redirects=True)
        assert resp1.status_code == 200

        db.session.expire_all()
        u = db.session.get(User, profile_user.id)
        old_filename = u.profile_image
        profile_dir = app.config["PROFILE_IMAGE_FOLDER"]
        old_path = os.path.join(profile_dir, old_filename)
        assert os.path.isfile(old_path)

        # 2차 업로드 (다른 이미지)
        png_data2 = BytesIO()
        img2 = Image.new("RGB", (15, 15), color="blue")
        img2.save(png_data2, format="PNG")
        png_data2.seek(0)
        data2 = {
            "nickname": "테스트",
            "email": "profile@example.com",
            "profile_image": (png_data2, "second.png"),
        }
        resp2 = logged_in_profile_client.post("/auth/profile", data=data2, follow_redirects=True)
        assert resp2.status_code == 200

        db.session.expire_all()
        u2 = db.session.get(User, profile_user.id)
        assert u2.profile_image != old_filename
        assert os.path.isfile(os.path.join(profile_dir, u2.profile_image))
        # 기존 파일 삭제 확인
        assert not os.path.isfile(old_path)
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v


def test_user_get_profile_image_url(app, app_ctx, profile_user):
    """User.get_profile_image_url() – profile_image 있으면 URL, 없으면 None."""
    assert profile_user.profile_image is None
    assert profile_user.get_profile_image_url() is None

    profile_user.profile_image = "test_123.jpg"
    db.session.commit()
    db.session.expire_all()
    u = db.session.get(User, profile_user.id)
    with app.test_request_context():
        url = u.get_profile_image_url()
    assert url is not None
    assert "media/profiles" in url or "test_123" in url
