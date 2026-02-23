# 단위 테스트 – 비디오 시청 (실제 DB instance/wetube.db 반영)
# 실행: pytest tests/test_watch_real_db.py -v
# ※ 실제 DB의 videos.views가 1 증가합니다.

import pytest
from sqlalchemy import text

from app import db
from app.models import User, Video


def test_watch_increments_views_in_real_db(real_client, real_app_ctx):
    """
    실제 DB(instance/wetube.db)에서 비디오 시청 시 조회수 1 증가 반영 확인.
    - DB에 비디오가 있으면 해당 비디오 사용, 없으면 생성 후 시청 테스트.
    - videos 테이블의 views 컬럼이 1 증가하는지 확인.
    """
    # 실제 DB에서 첫 번째 비디오 가져오기 (없으면 생성)
    video = Video.query.first()
    if video is None:
        user = db.session.get(User, 1)
        if user is None:
            pytest.skip("user_id=1이 없습니다. 앱을 한 번 실행해 기본 유저를 생성하세요.")
        video = Video(
            title="실제 DB 시청 테스트 영상",
            video_path="real_db_test.mp4",
            user_id=user.id,
            views=0,
        )
        db.session.add(video)
        db.session.commit()

    before_views = video.views

    # 시청 요청 (GET /watch/<id>) → DB에 조회수 1 증가 반영
    resp = real_client.get(f"/watch/{video.id}")
    assert resp.status_code == 200

    # DB에서 직접 조회해 조회수 1 증가 반영 확인
    row = db.session.execute(
        text("SELECT views FROM videos WHERE id = :id"),
        {"id": video.id},
    ).fetchone()
    assert row is not None
    assert row[0] == before_views + 1, f"videos.views가 {before_views} → {before_views + 1}로 DB에 반영되어야 함"
