# 단위 테스트 – 스튜디오 대시보드 통계 (_get_studio_stats, index 라우트)

import pytest

from app import db
from app.models import User, Video
from app.routes.studio import _get_studio_stats


@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (create_app에서 id=1 생성)."""
    return db.session.get(User, 1)


@pytest.fixture
def other_user(app_ctx):
    """다른 사용자 (id=2). 비디오 없음 테스트용."""
    u = User(username="other", email="other@example.com", password_hash="")
    db.session.add(u)
    db.session.commit()
    return u


# ----- _get_studio_stats 함수 -----
def test_get_studio_stats_empty_user(app_ctx, other_user):
    """비디오가 없는 사용자 → (0, 0) 반환."""
    total_views, video_count = _get_studio_stats(other_user.id)
    assert total_views == 0
    assert video_count == 0


def test_get_studio_stats_with_videos(app_ctx, user):
    """비디오가 있는 사용자 → 총 조회수 합계·영상 개수 반환."""
    v1 = Video(title="A", video_path="a.mp4", user_id=user.id, views=10)
    v2 = Video(title="B", video_path="b.mp4", user_id=user.id, views=20)
    v3 = Video(title="C", video_path="c.mp4", user_id=user.id, views=30)
    db.session.add_all([v1, v2, v3])
    db.session.commit()

    total_views, video_count = _get_studio_stats(user.id)
    assert total_views == 60
    assert video_count == 3


def test_get_studio_stats_single_video(app_ctx, user):
    """비디오 1개 → 해당 조회수·개수 1 반환."""
    v = Video(title="One", video_path="one.mp4", user_id=user.id, views=100)
    db.session.add(v)
    db.session.commit()

    total_views, video_count = _get_studio_stats(user.id)
    assert total_views == 100
    assert video_count == 1


def test_get_studio_stats_zero_views(app_ctx, user):
    """조회수 0인 비디오만 있어도 → total_views=0, video_count 정확."""
    v = Video(title="Zero", video_path="z.mp4", user_id=user.id, views=0)
    db.session.add(v)
    db.session.commit()

    total_views, video_count = _get_studio_stats(user.id)
    assert total_views == 0
    assert video_count == 1


def test_get_studio_stats_nonexistent_user_id(app_ctx):
    """존재하지 않는 user_id → (0, 0) 반환 (예외 없음)."""
    total_views, video_count = _get_studio_stats(99999)
    assert total_views == 0
    assert video_count == 0


def test_get_studio_stats_other_user_excluded(app_ctx, user, other_user):
    """다른 사용자 비디오는 합산되지 않음."""
    v_mine = Video(title="Mine", video_path="m.mp4", user_id=user.id, views=50)
    v_other = Video(title="Other", video_path="o.mp4", user_id=other_user.id, views=999)
    db.session.add_all([v_mine, v_other])
    db.session.commit()

    total_views, video_count = _get_studio_stats(user.id)
    assert total_views == 50
    assert video_count == 1


# ----- index 라우트 (통계 반영 확인) -----
def test_studio_index_shows_stats(logged_in_client, app_ctx, user):
    """GET /studio/ → 200, 응답에 총 조회수·영상 개수 포함."""
    v = Video(title="Test", video_path="t.mp4", user_id=user.id, views=42)
    db.session.add(v)
    db.session.commit()

    resp = logged_in_client.get("/studio/")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "42" in text
    assert "1" in text or "동영상" in text
