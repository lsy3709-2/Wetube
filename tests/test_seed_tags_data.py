# 시드 테스트 – videos, tags, video_tags 테이블에 임시 데이터 삽입
# 실행: pytest tests/test_seed_tags_data.py -v
# ※ 실제 DB(instance/wetube.db)에 데이터가 저장됩니다.

import os

import pytest

from app import db
from app.models import Tag, User, Video


# 시드할 태그 목록
SEED_TAGS = ["Python", "Flask", "튜토리얼", "WeTube", "동영상"]


def _seed_videos_from_uploads(app, user_id):
    """uploads/videos 폴더의 파일을 videos 테이블에 등록. 없으면 샘플 1개 생성."""
    video_folder = app.config.get("VIDEO_FOLDER", "")
    existing_paths = {v.video_path for v in Video.query.all()}

    added = 0
    if video_folder and os.path.isdir(video_folder):
        for i, fn in enumerate(sorted(os.listdir(video_folder)), 1):
            if not fn.lower().endswith((".mp4", ".webm", ".mov")):
                continue
            if fn in existing_paths:
                continue
            v = Video(
                title=f"시드 동영상 {i}",
                video_path=fn,
                thumbnail_path=None,
                user_id=user_id,
            )
            db.session.add(v)
            existing_paths.add(fn)
            added += 1

    if added == 0 and Video.query.count() == 0:
        v = Video(title="시드 샘플 동영상", video_path="seed_sample.mp4", user_id=user_id)
        db.session.add(v)
        added = 1
    if added > 0:
        db.session.commit()
    return Video.query.first()


def test_seed_videos_tags_video_tags(real_app_ctx):
    """
    videos, tags, video_tags 테이블 시드.
    1) videos가 비어 있으면 uploads/videos 기반으로 등록, 없으면 샘플 1개 생성
    2) tags 추가
    3) video_tags로 첫 번째 비디오에 태그 연결
    """
    user = db.session.get(User, 1)
    if user is None:
        pytest.skip("user_id=1이 없습니다. 앱을 한 번 실행해 기본 유저를 생성하세요.")

    # 1) videos 테이블 시드
    video = _seed_videos_from_uploads(real_app_ctx, user.id)
    assert video is not None, "videos 테이블에 레코드가 없습니다."

    # 2) tags 테이블 시드
    for name in SEED_TAGS:
        if Tag.query.filter_by(name=name).first() is None:
            db.session.add(Tag(name=name))
    db.session.commit()

    # 3) video_tags 연결
    video.save_tags(", ".join(SEED_TAGS))

    # 검증
    assert Video.query.count() >= 1
    assert Tag.query.count() >= len(SEED_TAGS)
    assert len(video.tags) >= len(SEED_TAGS)
