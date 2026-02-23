#!/usr/bin/env python
"""
DB 시드 스크립트 – videos, tags, video_tags 테이블에 임시 데이터 삽입.
실행: python scripts/seed_db.py
※ 프로젝트 루트(c:\Wetube\ch05)에서 실행하세요.
"""
import os
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Tag, User, Video

SEED_TAGS = ["Python", "Flask", "튜토리얼", "WeTube", "동영상"]


def seed_videos_from_uploads(app, user_id):
    """uploads/videos 폴더의 파일을 videos 테이블에 등록."""
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


def main():
    app = create_app()
    with app.app_context():
        user = db.session.get(User, 1)
        if user is None:
            print("오류: user_id=1이 없습니다. flask run으로 앱을 한 번 실행해주세요.")
            sys.exit(1)

        # 1) videos 시드
        video = seed_videos_from_uploads(app, user.id)
        if video:
            print(f"videos: {Video.query.count()}개 (예: id={video.id} '{video.title}')")
        else:
            print("videos: 레코드 없음 (uploads/videos 폴더 확인)")

        # 2) tags 시드
        for name in SEED_TAGS:
            if Tag.query.filter_by(name=name).first() is None:
                db.session.add(Tag(name=name))
        db.session.commit()
        print(f"tags: {Tag.query.count()}개")

        # 3) video_tags 연결
        if video:
            video.save_tags(", ".join(SEED_TAGS))
            print(f"video_tags: video_id={video.id}에 태그 {len(SEED_TAGS)}개 연결")

    print("시드 완료.")


if __name__ == "__main__":
    main()
