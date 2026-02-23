"""
비디오 좋아요 블루프린트 – 좋아요 토글·상태 조회 API.

- POST /video/<video_id>/like: 좋아요 토글 (누름 → 해제, 안 눌림 → 추가)
- GET /video/<video_id>/like/status: 현재 사용자 좋아요 여부 + 총 좋아요 수 반환
"""

from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy import delete, insert, select

from app import db
from app.models import Video
from app.models.video import video_likes

likes_bp = Blueprint("likes", __name__)


def _get_likes_count(video_id):
    """
    video_likes 테이블에서 해당 영상의 좋아요 개수를 세어 반환.
    videos.likes 컬럼과 동기화를 위해 실제 중간 테이블 행 수를 사용.
    """
    result = db.session.execute(
        select(db.func.count()).select_from(video_likes).where(video_likes.c.video_id == video_id)
    )
    return result.scalar() or 0


def _is_user_liked(video_id, user_id):
    """
    현재 사용자가 해당 영상에 좋아요를 눌렀는지 video_likes 테이블에서 조회.
    """
    if not user_id:
        return False
    result = db.session.execute(
        select(1).where(
            video_likes.c.video_id == video_id,
            video_likes.c.user_id == user_id,
        )
    )
    return result.scalar() is not None


# ----- POST /video/<video_id>/like: 좋아요 토글 -----
@likes_bp.route("/video/<int:video_id>/like", methods=["POST"])
@login_required
def toggle_like(video_id):
    """
    좋아요 토글 API.
    - 이미 좋아요를 눌렀으면: video_likes에서 삭제 (좋아요 해제)
    - 아직 누르지 않았으면: video_likes에 추가 (좋아요)

    처리 후 video.likes 카운트를 갱신하고 JSON 응답 반환.
    """
    # 1) 영상 존재 여부 확인
    video = db.session.get(Video, video_id)
    if video is None:
        return jsonify({"success": False, "error": "영상을 찾을 수 없습니다."}), 404

    user_id = current_user.id

    # 2) video_likes 테이블에서 현재 사용자의 좋아요 여부 조회
    already_liked = _is_user_liked(video_id, user_id)

    if already_liked:
        # 3-a) 이미 좋아요를 눌렀다면 → 삭제 (토글 off)
        db.session.execute(
            delete(video_likes).where(
                video_likes.c.video_id == video_id,
                video_likes.c.user_id == user_id,
            )
        )
        is_liked_after = False
    else:
        # 3-b) 아직 누르지 않았다면 → 추가 (토글 on)
        stmt = insert(video_likes).values(video_id=video_id, user_id=user_id)
        db.session.execute(stmt)
        is_liked_after = True

    # 4) video.likes 컬럼 갱신 (실제 video_likes 행 수와 동기화)
    new_count = _get_likes_count(video_id)
    video.likes = new_count
    db.session.commit()

    # 5) JSON 응답 반환
    return jsonify({
        "success": True,
        "is_liked": is_liked_after,
        "likes_count": new_count,
    })


# ----- GET /video/<video_id>/like/status: 좋아요 상태 조회 -----
@likes_bp.route("/video/<int:video_id>/like/status", methods=["GET"])
def like_status(video_id):
    """
    영상 페이지 접속 시 호출되는 API.
    현재 로그인한 사용자의 좋아요 여부(is_liked)와
    해당 영상의 총 좋아요 수(likes_count)를 반환.

    비로그인 사용자도 호출 가능 (is_liked는 항상 False).
    """
    # 1) 영상 존재 여부 확인
    video = db.session.get(Video, video_id)
    if video is None:
        return jsonify({"success": False, "error": "영상을 찾을 수 없습니다."}), 404

    # 2) 로그인한 사용자인지 확인 후 좋아요 여부 조회
    user_id = current_user.id if current_user.is_authenticated else None
    is_liked = _is_user_liked(video_id, user_id)

    # 3) 좋아요 수: video_likes 테이블의 행 수 (video.likes와 동기화됨)
    likes_count = _get_likes_count(video_id)

    # 4) JSON 응답 반환
    return jsonify({
        "success": True,
        "is_liked": is_liked,
        "likes_count": likes_count,
    })
