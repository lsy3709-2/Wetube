# 단위 테스트 – 비디오 시청 (watch 라우트, 조회수, 플레이어)

import pytest
from sqlalchemy import text

from app import db
from app.models import User, Video


@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (create_app에서 id=1 생성)."""
    return db.session.get(User, 1)


@pytest.fixture
def video(app_ctx, user):
    """테스트용 비디오 (시청 대상)."""
    v = Video(
        title="시청 테스트 영상",
        description="설명",
        video_path="test_video.mp4",
        thumbnail_path="test_thumb.png",
        user_id=user.id,
        views=0,
    )
    db.session.add(v)
    db.session.commit()
    return v


# ----- watch 라우트 -----
def test_watch_returns_200_when_video_exists(client, app_ctx, video):
    """GET /watch/<id> → 200, 응답에 비디오 제목 포함."""
    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "시청 테스트 영상" in text


def test_watch_returns_404_when_video_not_found(client):
    """존재하지 않는 비디오 ID → 404."""
    resp = client.get("/watch/99999")
    assert resp.status_code == 404


def test_watch_increments_views(client, app_ctx, video):
    """시청 시 비디오 테이블(videos)의 views 컬럼이 1씩 증가하는지 DB에서 직접 확인."""
    assert video.views == 0

    # 시청 요청 (GET /watch/<id>)
    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200

    # DB에서 직접 조회해 조회수 1 증가 반영 확인
    updated = Video.query.get(video.id)
    assert updated.views == 1, "videos 테이블에 조회수 1이 반영되어야 함"

    # 두 번째 시청 시 조회수 2
    client.get(f"/watch/{video.id}")
    updated = Video.query.get(video.id)
    assert updated.views == 2, "videos 테이블에 조회수 2가 반영되어야 함"


def test_watch_videos_table_views_reflected(client, app_ctx, video):
    """시청 후 videos 테이블의 views 컬럼이 DB에 반영되는지 raw SQL로 확인."""
    client.get(f"/watch/{video.id}")
    row = db.session.execute(
        text("SELECT views FROM videos WHERE id = :id"),
        {"id": video.id},
    ).fetchone()
    assert row is not None
    assert row[0] == 1, "videos.views가 1로 DB에 저장되어야 함"


def test_watch_contains_video_player(client, app_ctx, video):
    """응답에 HTML5 video 태그 및 비디오 URL 포함."""
    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "<video" in text
    assert "/media/videos/" in text
    assert "test_video.mp4" in text


def test_watch_contains_poster_thumbnail(client, app_ctx, video):
    """응답에 poster(썸네일) URL 포함."""
    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "poster=" in text
    assert "/media/thumbnails/" in text
    assert "test_thumb.png" in text


def test_watch_shows_updated_view_count(client, app_ctx, video):
    """시청 후 화면에 갱신된 조회수 표시."""
    client.get(f"/watch/{video.id}")
    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "조회수 2회" in text


# ----- Video 모델 get_video_url, get_thumbnail_url -----
def test_get_video_url_returns_media_path(app, app_ctx, video):
    """get_video_url() → /media/videos/<filename> 형태."""
    with app.test_request_context():
        url = video.get_video_url()
    assert "/media/videos/" in url
    assert video.video_path in url


def test_get_thumbnail_url_returns_url_when_exists(app, app_ctx, video):
    """썸네일 있으면 get_thumbnail_url() → URL 반환."""
    with app.test_request_context():
        url = video.get_thumbnail_url()
    assert url is not None
    assert "/media/thumbnails/" in url
    assert video.thumbnail_path in url


def test_get_thumbnail_url_returns_none_when_no_thumbnail(app_ctx, user):
    """썸네일 없으면 get_thumbnail_url() → None."""
    v = Video(title="NoThumb", video_path="x.mp4", user_id=user.id, thumbnail_path=None)
    db.session.add(v)
    db.session.commit()
    assert v.get_thumbnail_url() is None
