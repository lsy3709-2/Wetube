# 단위 테스트 – 비디오 좋아요 API (likes 블루프린트)

import pytest
from sqlalchemy import insert

from app import db
from app.models import User, Video
from app.models.video import video_likes


# ----- 공통 픽스처 -----
@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (create_app에서 id=1 생성)."""
    return db.session.get(User, 1)


@pytest.fixture
def other_user(app_ctx):
    """다른 사용자 (좋아요 토글·다중 유저 테스트용)."""
    u = User(username="likes_other", email="likes_other@example.com")
    u.set_password("secret")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def video(app_ctx, user):
    """테스트용 비디오 (좋아요 대상)."""
    v = Video(
        title="좋아요 테스트 영상",
        description="설명",
        video_path="like_test.mp4",
        thumbnail_path="like_thumb.png",
        user_id=user.id,
        views=0,
        likes=0,
    )
    db.session.add(v)
    db.session.commit()
    return v


def _login_client(client, username, password):
    """클라이언트를 해당 유저로 로그인 처리."""
    client.post(
        "/auth/login",
        data={"login_id": username, "password": password},
        follow_redirects=True,
    )


# ===========================================================================
# GET /video/<video_id>/like/status – 좋아요 상태 조회
# ===========================================================================


def test_like_status_returns_200_when_video_exists(client, app_ctx, video):
    """영상 존재 시 → 200, JSON 응답."""
    resp = client.get(f"/video/{video.id}/like/status")
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    data = resp.get_json()
    assert data["success"] is True
    assert "is_liked" in data
    assert "likes_count" in data


def test_like_status_anon_user_is_liked_false(client, app_ctx, video):
    """비로그인 사용자 → is_liked 항상 False."""
    resp = client.get(f"/video/{video.id}/like/status")
    data = resp.get_json()
    assert data["is_liked"] is False
    assert data["likes_count"] == 0


def test_like_status_logged_in_not_liked(client, app_ctx, video, other_user):
    """로그인했지만 좋아요 안 함 → is_liked False."""
    _login_client(client, "likes_other", "secret")
    resp = client.get(f"/video/{video.id}/like/status")
    data = resp.get_json()
    assert data["is_liked"] is False
    assert data["likes_count"] == 0


def test_like_status_logged_in_liked(client, app_ctx, video, other_user):
    """로그인 후 좋아요 누른 상태 → is_liked True, likes_count 반영."""
    # video_likes에 직접 추가 (로그인 전 좋아요 상태 시뮬레이션)
    db.session.execute(
        insert(video_likes).values(video_id=video.id, user_id=other_user.id)
    )
    db.session.commit()

    _login_client(client, "likes_other", "secret")
    resp = client.get(f"/video/{video.id}/like/status")
    data = resp.get_json()
    assert data["is_liked"] is True
    assert data["likes_count"] == 1


def test_like_status_404_when_video_not_found(client):
    """존재하지 않는 비디오 ID → 404."""
    resp = client.get("/video/99999/like/status")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False
    assert "error" in data


# ===========================================================================
# POST /video/<video_id>/like – 좋아요 토글 (login_required)
# ===========================================================================


def test_toggle_like_anon_returns_redirect(client, app_ctx, video):
    """비로그인 시 POST → 302, 로그인 페이지로 리다이렉트."""
    resp = client.post(f"/video/{video.id}/like", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in (resp.location or "")


def test_toggle_like_first_toggle_adds_like(logged_in_client, app_ctx, video):
    """로그인 후 첫 토글 → 좋아요 추가, is_liked=True, likes_count=1."""
    resp = logged_in_client.post(
        f"/video/{video.id}/like",
        follow_redirects=False,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["is_liked"] is True
    assert data["likes_count"] == 1


def test_toggle_like_second_toggle_removes_like(logged_in_client, app_ctx, video):
    """로그인 후 두 번째 토글 → 좋아요 해제, is_liked=False, likes_count=0."""
    # 첫 번째: 좋아요 추가
    logged_in_client.post(f"/video/{video.id}/like", follow_redirects=False)

    # 두 번째: 좋아요 해제
    resp = logged_in_client.post(
        f"/video/{video.id}/like",
        follow_redirects=False,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["is_liked"] is False
    assert data["likes_count"] == 0


def test_toggle_like_updates_video_likes_column(logged_in_client, app_ctx, video):
    """토글 후 videos.likes 컬럼이 DB에 반영되는지 확인."""
    assert video.likes == 0

    # 좋아요 추가
    logged_in_client.post(f"/video/{video.id}/like", follow_redirects=False)
    video_updated = db.session.get(Video, video.id)
    assert video_updated.likes == 1

    # 좋아요 해제
    logged_in_client.post(f"/video/{video.id}/like", follow_redirects=False)
    video_updated = db.session.get(Video, video.id)
    assert video_updated.likes == 0


def test_toggle_like_404_when_video_not_found(logged_in_client):
    """존재하지 않는 비디오 ID로 POST → 404."""
    resp = logged_in_client.post("/video/99999/like", follow_redirects=False)
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False
    assert "error" in data


def test_toggle_like_multiple_users_count_correct(logged_in_client, app_ctx, video, other_user):
    """여러 유저가 좋아요 시 likes_count 정확히 반영."""
    # default 유저로 로그인한 상태에서 좋아요 1회
    logged_in_client.post(f"/video/{video.id}/like", follow_redirects=False)

    # other_user로 로그인해서 좋아요 추가
    logged_in_client.post(
        "/auth/login",
        data={"login_id": "likes_other", "password": "secret"},
        follow_redirects=True,
    )
    resp = logged_in_client.post(
        f"/video/{video.id}/like",
        follow_redirects=False,
    )
    data = resp.get_json()
    assert data["success"] is True
    assert data["is_liked"] is True
    assert data["likes_count"] == 2
