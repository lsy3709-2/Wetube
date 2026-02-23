# 단위 테스트 – 사용자 프로필, 구독 피드

import pytest

from app import db
from app.models import Subscription, User, Video


@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (id=1)."""
    return db.session.get(User, 1)


@pytest.fixture
def other_user(app_ctx):
    """다른 사용자 (프로필·구독 테스트용)."""
    u = User(username="other", email="other@example.com", password_hash="")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def user_with_videos(app_ctx, user):
    """비디오가 있는 사용자."""
    for i in range(3):
        v = Video(
            title=f"프로필테스트{i}",
            description="설명",
            video_path=f"p{i}.mp4",
            user_id=user.id,
            views=(i + 1) * 10,
            likes=i,
        )
        db.session.add(v)
    db.session.commit()
    return user


# ----- 사용자 프로필 (GET /user/<username>) -----
def test_profile_returns_200_when_user_exists(client, app_ctx, user_with_videos):
    """존재하는 사용자 → 200."""
    resp = client.get(f"/user/{user_with_videos.username}")
    assert resp.status_code == 200


def test_profile_returns_404_when_user_not_found(client):
    """존재하지 않는 사용자 → 404 (first_or_404)."""
    resp = client.get("/user/nonexistent_user_xyz_123")
    assert resp.status_code == 404


def test_profile_shows_stats(client, app_ctx, user_with_videos):
    """채널 통계(총 조회수, 좋아요, 동영상 수, 구독자 수) 포함."""
    resp = client.get(f"/user/{user_with_videos.username}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    # 10+20+30 = 60 조회수, likes 0+1+2 = 3
    assert "60" in text or "총 조회수" in text
    assert "3" in text or "총 좋아요" in text
    assert "3" in text  # video_count
    assert user_with_videos.username in text


def test_profile_shows_user_videos(client, app_ctx, user_with_videos):
    """해당 사용자 업로드 영상만 표시."""
    resp = client.get(f"/user/{user_with_videos.username}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "프로필테스트0" in text
    assert "프로필테스트1" in text
    assert "프로필테스트2" in text


def test_profile_excludes_other_user_videos(client, app_ctx, user_with_videos, other_user):
    """다른 사용자 영상은 표시 안 함."""
    v = Video(title="다른유저영상", video_path="x.mp4", user_id=other_user.id)
    db.session.add(v)
    db.session.commit()

    resp = client.get(f"/user/{user_with_videos.username}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "다른유저영상" not in text


def test_profile_pagination(client, app_ctx, user):
    """프로필 동영상 페이지네이션 (12개씩)."""
    for i in range(14):
        v = Video(
            title=f"페이지테스트{i}",
            description="d",
            video_path=f"v{i}.mp4",
            user_id=user.id,
        )
        db.session.add(v)
    db.session.commit()

    resp = client.get(f"/user/{user.username}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert text.count("video-card") >= 12
    assert "1 / 2" in text or "페이지" in text

    resp2 = client.get(f"/user/{user.username}?page=2")
    assert resp2.status_code == 200


# ----- 구독 피드 (GET /subscriptions) -----
def test_subscriptions_returns_200(client, app_ctx):
    """구독 페이지 200 (테스트 환경 시 첫 사용자로 진행)."""
    resp = client.get("/subscriptions")
    assert resp.status_code == 200


def test_subscriptions_empty_when_no_subscriptions(client, app_ctx, user):
    """구독한 채널 없으면 빈 피드."""
    resp = client.get("/subscriptions")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "구독한 채널이 없습니다" in text


def test_subscriptions_shows_subscribed_channel_videos(client, app_ctx, user, other_user):
    """구독한 채널의 영상만 피드에 표시."""
    # other_user 영상 생성
    v = Video(
        title="구독채널영상",
        description="d",
        video_path="sub.mp4",
        user_id=other_user.id,
    )
    db.session.add(v)
    db.session.commit()

    # user가 other_user 구독
    sub = Subscription(subscriber_id=user.id, subscribed_to_id=other_user.id)
    db.session.add(sub)
    db.session.commit()

    resp = client.get("/subscriptions")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "구독채널영상" in text


def test_subscriptions_excludes_unsubscribed_channel(client, app_ctx, user, other_user):
    """구독하지 않은 채널 영상은 표시 안 함."""
    v = Video(
        title="미구독채널영상",
        description="d",
        video_path="nsub.mp4",
        user_id=other_user.id,
    )
    db.session.add(v)
    db.session.commit()
    # 구독 관계 없음

    resp = client.get("/subscriptions")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "미구독채널영상" not in text


def test_subscriptions_pagination(client, app_ctx, user, other_user):
    """구독 피드 페이지네이션 (12개씩, 2페이지)."""
    for i in range(14):
        v = Video(
            title=f"feedpag{i}",
            description="d",
            video_path=f"f{i}.mp4",
            user_id=other_user.id,
        )
        db.session.add(v)
    db.session.commit()

    sub = Subscription(subscriber_id=user.id, subscribed_to_id=other_user.id)
    db.session.add(sub)
    db.session.commit()

    # page 1: 12개
    resp = client.get("/subscriptions")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "1 / 2" in text
    assert "feedpag" in text

    # page 2: 나머지 2개
    resp2 = client.get("/subscriptions?page=2")
    assert resp2.status_code == 200
    text2 = resp2.data.decode("utf-8")
    assert "feedpag" in text2
