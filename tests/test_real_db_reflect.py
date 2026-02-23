# 단위 테스트 – 실제 DB(instance/wetube.db)에 데이터 반영 후 sqlite로 확인
# 실행: pytest tests/test_real_db_reflect.py -v
# ※ 실행 후 sqlite3 instance/wetube.db 로 테이블 확인

import pytest
from sqlalchemy import text

from app import db
from app.models import Subscription, User, Video


@pytest.fixture
def real_db_data(real_app_ctx):
    """실제 DB에 테스트 데이터 생성 (users, videos, subscriptions)."""
    user1 = User.query.first()
    if not user1:
        pytest.skip("user 없음. 앱을 한 번 실행해 기본 유저를 생성하세요.")

    # 다른 유저 (구독 테스트용)
    user2 = User.query.filter_by(username="real_test_user").first()
    if not user2:
        user2 = User(username="real_test_user", email="realtest@example.com", password_hash="")
        db.session.add(user2)
        db.session.commit()

    # 비디오 생성 (user1, user2 각각)
    v1 = Video.query.filter_by(title="실제DB테스트_유저1").first()
    if not v1:
        v1 = Video(
            title="실제DB테스트_유저1",
            description="프로필/시청 테스트",
            video_path="real1.mp4",
            user_id=user1.id,
            views=0,
            likes=0,
        )
        db.session.add(v1)
        db.session.commit()

    v2 = Video.query.filter_by(title="실제DB테스트_유저2").first()
    if not v2:
        v2 = Video(
            title="실제DB테스트_유저2",
            description="구독 피드 테스트",
            video_path="real2.mp4",
            user_id=user2.id,
            views=0,
            likes=0,
        )
        db.session.add(v2)
        db.session.commit()

    # 구독: user1이 user2 구독
    sub = db.session.execute(
        text(
            "SELECT 1 FROM subscriptions WHERE subscriber_id = :sid AND subscribed_to_id = :tid"
        ),
        {"sid": user1.id, "tid": user2.id},
    ).fetchone()
    if not sub:
        s = Subscription(subscriber_id=user1.id, subscribed_to_id=user2.id)
        db.session.add(s)
        db.session.commit()

    return {"user1": user1, "user2": user2, "video1": v1, "video2": v2}


def test_watch_reflects_to_real_db(real_client, real_db_data):
    """시청 → videos.views DB 반영."""
    v = real_db_data["video1"]
    before = v.views
    real_client.get(f"/watch/{v.id}")
    row = db.session.execute(text("SELECT views FROM videos WHERE id = :id"), {"id": v.id}).fetchone()
    assert row[0] == before + 1


def test_profile_reads_from_real_db(real_client, real_db_data):
    """프로필 → user, stats DB 조회 반영."""
    u = real_db_data["user1"]
    resp = real_client.get(f"/user/{u.username}")
    assert resp.status_code == 200


def test_subscriptions_reads_from_real_db(real_client, real_db_data):
    """구독 피드 → subscriptions 기반 필터링."""
    resp = real_client.get("/subscriptions")
    assert resp.status_code == 200
    text_content = resp.data.decode("utf-8")
    assert "실제DB테스트_유저2" in text_content
