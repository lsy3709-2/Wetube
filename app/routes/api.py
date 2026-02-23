"""
REST API 블루프린트 – 웹/모바일 앱용 JSON API.

엔드포인트:
  - GET /api/videos (목록, 페이지네이션·검색·정렬)
  - GET /api/videos/<id> (상세 + 관련 동영상)
  - GET /api/tags/popular (인기 태그)
  - GET /api/tags/<tag_name>/videos (태그별 비디오)
  - GET /api/users/<username> (사용자 프로필 + 채널 통계)
  - GET /api/users/<username>/videos (사용자 업로드 비디오)
"""

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import joinedload

from flask import abort, Blueprint, jsonify, request

from app import db
from app.models import Tag, User, Video
from app.models.video import video_tags

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# 헬퍼: 비디오 → JSON 직렬화
# ---------------------------------------------------------------------------
def _video_to_dict(video):
    """비디오 객체를 API 응답용 딕셔너리로 변환."""
    return {
        "id": video.id,
        "title": video.title,
        "description": video.description or "",
        "category": video.category or "",
        "duration": video.duration,
        "views": video.views,
        "likes": video.likes,
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "video_url": video.get_video_url() if video.video_path else None,
        "thumbnail_url": video.get_thumbnail_url(),
        "channel": {
            "id": video.user.id if video.user else None,
            "username": video.user.username if video.user else "unknown",
        },
        "tags": [t.name for t in video.tags] if video.tags else [],
    }


def _pagination_meta(pagination):
    """paginate() 결과에서 메타 정보 추출."""
    return {
        "total_pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page,
        "total_items": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


# ---------------------------------------------------------------------------
# 관련 동영상 추천 알고리즘
# 1순위: 같은 태그, 2순위: 같은 카테고리, 3순위: 같은 작성자, 4순위: 인기순(조회수/좋아요)
# 조건: 현재 비디오 제외, 중복 없이 limit개
# ---------------------------------------------------------------------------
def get_related_videos(video_id, limit=5):
    """
    상세 조회 시 함께 보여줄 추천 비디오 목록 반환.
    우선순위: 같은 태그 > 같은 카테고리 > 같은 작성자 > 인기순.
    """
    current = db.session.get(Video, video_id)
    if not current:
        return []

    exclude_ids = {video_id}
    result = []
    seen_ids = set()

    def add_videos(q, max_take=None):
        """쿼리에서 limit 남은 개수만큼 추가 (중복·현재 비디오 제외)."""
        nonlocal result, seen_ids
        remaining = limit - len(result)
        if remaining <= 0 or (max_take is not None and max_take <= 0):
            return
        q = q.filter(Video.id.notin_(exclude_ids)).options(
            joinedload(Video.user), joinedload(Video.tags)
        )
        if seen_ids:
            q = q.filter(Video.id.notin_(seen_ids))
        take = min(remaining, limit) if max_take is None else min(remaining, max_take)
        rows = q.limit(take).all()
        for v in rows:
            if len(result) >= limit:
                break
            if v.id not in seen_ids:
                result.append(v)
                seen_ids.add(v.id)

    # 1순위: 같은 태그
    tag_ids = [t.id for t in current.tags] if current.tags else []
    if tag_ids:
        subq = (
            db.session.query(video_tags.c.video_id)
            .filter(video_tags.c.tag_id.in_(tag_ids))
            .filter(video_tags.c.video_id != video_id)
        )
        add_videos(Video.query.filter(Video.id.in_(subq)).order_by(Video.created_at.desc()))

    # 2순위: 같은 카테고리 (태그로 못 채운 경우)
    if len(result) < limit and current.category:
        add_videos(
            Video.query.filter(Video.category == current.category).order_by(Video.created_at.desc())
        )

    # 3순위: 같은 작성자
    if len(result) < limit and current.user_id:
        add_videos(
            Video.query.filter(Video.user_id == current.user_id).order_by(Video.created_at.desc())
        )

    # 4순위: 인기순 (조회수, 좋아요)
    if len(result) < limit:
        add_videos(Video.query.order_by(Video.views.desc(), Video.likes.desc()))

    return result[:limit]


# ===========================================================================
# 1. 비디오 API
# ===========================================================================


@api_bp.route("/videos", methods=["GET"], strict_slashes=False)
def list_videos():
    """
    비디오 목록. 페이지네이션, 정렬, 카테고리, 검색 지원.
    파라미터: page, per_page, sort, category, search
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    sort = request.args.get("sort", "latest", type=str).strip() or "latest"
    category = request.args.get("category", "", type=str).strip()
    search = request.args.get("search", "", type=str).strip()
    tag_name = request.args.get("tag", "", type=str).strip()

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 12

    query = Video.query.options(joinedload(Video.user), joinedload(Video.tags))

    # 태그 필터
    if tag_name:
        tag_obj = Tag.query.filter_by(name=tag_name).first()
        if tag_obj:
            query = query.join(video_tags).filter(video_tags.c.tag_id == tag_obj.id)
        else:
            query = query.filter(Video.id < 0)

    # 검색: 제목 또는 설명에 검색어 포함
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Video.title.ilike(pattern),
                and_(Video.description.isnot(None), Video.description.ilike(pattern)),
            )
        )

    # 카테고리 필터 (all 또는 빈 값이면 필터 없음)
    if category and category != "all":
        query = query.filter(Video.category == category)

    # 정렬
    if sort == "popular":
        query = query.order_by(Video.likes.desc(), Video.views.desc())
    elif sort == "views":
        query = query.order_by(Video.views.desc())
    else:
        query = query.order_by(Video.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page)
    items = [_video_to_dict(v) for v in pagination.items]

    return jsonify(
        {
            "success": True,
            "items": items,
            "meta": _pagination_meta(pagination),
        }
    )


@api_bp.route("/videos/<int:video_id>", methods=["GET"], strict_slashes=False)
def video_detail(video_id):
    """
    비디오 상세 조회. 조회수 +1, 관련 동영상 포함.
    """
    video = Video.query.options(joinedload(Video.user), joinedload(Video.tags)).filter(Video.id == video_id).first()
    if not video:
        abort(404)

    # 조회수 증가
    video.views += 1
    db.session.commit()

    related = get_related_videos(video_id, limit=5)
    related_items = [_video_to_dict(v) for v in related]

    return jsonify(
        {
            "success": True,
            "item": _video_to_dict(video),
            "related_videos": related_items,
        }
    )


# ===========================================================================
# 2. 태그 API
# ===========================================================================


@api_bp.route("/tags/popular", methods=["GET"])
def popular_tags():
    """
    비디오가 가장 많이 등록된 상위 N개 태그.
    파라미터: limit (기본 10)
    """
    limit = request.args.get("limit", 10, type=int)
    if limit < 1 or limit > 50:
        limit = 10

    tags = (
        db.session.query(Tag)
        .join(video_tags)
        .group_by(Tag.id)
        .order_by(func.count(video_tags.c.video_id).desc())
        .limit(limit)
        .all()
    )

    items = [{"id": t.id, "name": t.name} for t in tags]

    return jsonify({"success": True, "items": items})


@api_bp.route("/tags/<tag_name>/videos", methods=["GET"])
def tag_videos(tag_name):
    """
    특정 태그가 달린 비디오 목록. 최신순, 페이지네이션.
    """
    tag_obj = Tag.query.filter_by(name=tag_name).first_or_404()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 12

    pagination = (
        Video.query.options(joinedload(Video.user), joinedload(Video.tags))
        .join(video_tags)
        .filter(video_tags.c.tag_id == tag_obj.id)
        .order_by(Video.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )
    items = [_video_to_dict(v) for v in pagination.items]

    return jsonify(
        {
            "success": True,
            "tag": {"id": tag_obj.id, "name": tag_obj.name},
            "items": items,
            "meta": _pagination_meta(pagination),
        }
    )


# ===========================================================================
# 3. 사용자 API
# ===========================================================================


@api_bp.route("/users/<username>", methods=["GET"])
def user_profile(username):
    """
    사용자 프로필 + 채널 통계 (총 조회수, 총 좋아요, 구독자 수).
    """
    user = User.query.filter_by(username=username).first_or_404()

    stats_row = (
        db.session.query(
            func.coalesce(func.sum(Video.views), 0).label("total_views"),
            func.coalesce(func.sum(Video.likes), 0).label("total_likes"),
            func.count(Video.id).label("video_count"),
        )
        .filter(Video.user_id == user.id)
        .first()
    )
    subscriber_count = user.subscribers_rel.count()

    return jsonify(
        {
            "success": True,
            "item": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname or user.username,
                "email": user.email,
                "profile_image": user.profile_image,
                "stats": {
                    "total_views": int(stats_row.total_views or 0),
                    "total_likes": int(stats_row.total_likes or 0),
                    "video_count": int(stats_row.video_count or 0),
                    "subscriber_count": subscriber_count,
                },
            },
        }
    )


@api_bp.route("/users/<username>/videos", methods=["GET"])
def user_videos(username):
    """
    해당 사용자가 업로드한 비디오 목록. 페이지네이션.
    """
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 12

    pagination = (
        Video.query.options(joinedload(Video.user), joinedload(Video.tags))
        .filter(Video.user_id == user.id)
        .order_by(Video.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )
    items = [_video_to_dict(v) for v in pagination.items]

    return jsonify(
        {
            "success": True,
            "user": {"id": user.id, "username": user.username},
            "items": items,
            "meta": _pagination_meta(pagination),
        }
    )
