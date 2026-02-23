"""메인 라우트 – DB·미디어 연동."""

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import joinedload

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_from_directory, url_for

from app import db
from app.models import Comment, Subscription, Tag, User, Video
from app.models.video import video_tags

main_bp = Blueprint("main", __name__)


def _get_popular_tags(limit=12):
    """동영상이 연결된 태그를 비디오 수 기준으로 정렬해 반환."""
    return (
        db.session.query(Tag)
        .join(video_tags)
        .group_by(Tag.id)
        .order_by(func.count(video_tags.c.video_id).desc())
        .limit(limit)
        .all()
    )


# ----- 업로드된 미디어 서빙 (비디오·썸네일 URL) -----
@main_bp.route("/media/videos/<path:filename>")
def media_video(filename):
    """업로드된 비디오 파일 응답."""
    return send_from_directory(current_app.config["VIDEO_FOLDER"], filename)


@main_bp.route("/media/thumbnails/<path:filename>")
def media_thumbnail(filename):
    """업로드된 썸네일 이미지 응답."""
    return send_from_directory(current_app.config["THUMBNAIL_FOLDER"], filename)


@main_bp.route("/media/profiles/<path:filename>")
def media_profile(filename):
    """업로드된 프로필 이미지 응답."""
    return send_from_directory(current_app.config["PROFILE_IMAGE_FOLDER"], filename)


@main_bp.route("/")
def index():
    category = (request.args.get("category") or "all").strip() or "all"
    sort = (request.args.get("sort") or "latest").strip() or "latest"
    tag_filter = request.args.get("tag", "").strip()

    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    per_page = 12
    q = Video.query.options(joinedload(Video.user))
    # category가 all 또는 비어 있으면 카테고리 필터 없음 (NULL/빈 카테고리 영상도 포함)
    if category and category != "all":
        q = q.filter(Video.category == category)
    if tag_filter:
        tag_obj = Tag.query.filter_by(name=tag_filter).first()
        if tag_obj:
            q = q.join(video_tags).filter(video_tags.c.tag_id == tag_obj.id)
        else:
            q = q.filter(Video.id < 0)
    if sort == "popular":
        q = q.order_by(Video.likes.desc(), Video.views.desc())
    elif sort == "views":
        q = q.order_by(Video.views.desc())
    else:
        q = q.order_by(Video.created_at.desc())
    videos = q.paginate(page=page, per_page=per_page)
    popular_tags = _get_popular_tags()
    return render_template(
        "main/index.html",
        videos=videos,
        popular_tags=popular_tags,
        current_tag=tag_filter or None,
    )


@main_bp.route("/watch/<int:video_id>")
def watch(video_id):
    video = Video.query.get_or_404(video_id)
    video.views += 1
    db.session.commit()
    user = db.session.get(User, video.user_id) if video.user_id else None
    channel_name = user.username if user else "default"
    related = (
        Video.query.options(joinedload(Video.user))
        .filter(Video.id != video_id)
        .order_by(Video.created_at.desc())
        .limit(10)
        .all()
    )
    current = _get_subscriptions_user()
    is_subscribed = _is_subscribed(current.id if current else None, video.user_id)
    subscriber_count = user.subscribers_rel.count() if user else 0

    # 최상위 댓글만 작성 시간 오름차순으로 조회 (대댓글은 replies로 포함)
    top_comments = (
        Comment.query.filter_by(video_id=video_id, parent_id=None)
        .options(db.joinedload(Comment.user), db.joinedload(Comment.replies).joinedload(Comment.user))
        .order_by(Comment.created_at.asc())
        .all()
    )
    total_comments = sum(1 + len(c.replies) for c in top_comments)

    return render_template(
        "main/watch.html",
        video=video,
        channel_name=channel_name,
        related_videos=related,
        is_subscribed=is_subscribed,
        subscriber_count=subscriber_count,
        comments=top_comments,
        total_comments=total_comments,
    )


@main_bp.route("/search", methods=["GET"])
def search():
    """
    비디오 검색 – 키워드(q), 카테고리(category), 정렬(sort), 페이지(page) 지원.
    """
    q_param = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "latest").strip() or "latest"
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    # 검색어 없을 때: 빈 결과
    if not q_param:
        pagination = None
    else:
        query = Video.query.options(joinedload(Video.user))

        # ➂ 복합 키워드 검색: 제목 또는 설명에 검색어 포함
        pattern = f"%{q_param}%"
        keyword_filter = or_(
            Video.title.ilike(pattern),
            and_(Video.description.isnot(None), Video.description.ilike(pattern)),
        )
        query = query.filter(keyword_filter)

        # ➃ 카테고리 필터
        if category:
            query = query.filter(Video.category == category)

        # ➄ 동적 정렬
        if sort == "popular":
            query = query.order_by(Video.likes.desc(), Video.views.desc())
        elif sort == "views":
            query = query.order_by(Video.views.desc())
        else:
            # latest (기본값): 최신순
            query = query.order_by(Video.created_at.desc())

        # ➅ 페이지네이션 (한 페이지당 12개)
        pagination = query.paginate(page=page, per_page=12)

    return render_template(
        "main/search.html",
        videos=pagination,
        q=q_param,
        category=category,
        sort=sort,
    )


def _is_subscribed(subscriber_id, subscribed_to_id):
    """구독 관계 여부 확인."""
    if not subscriber_id or not subscribed_to_id or subscriber_id == subscribed_to_id:
        return False
    return (
        Subscription.query.filter_by(
            subscriber_id=subscriber_id,
            subscribed_to_id=subscribed_to_id,
        ).first()
        is not None
    )


def _get_subscriptions_user():
    """
    구독 피드에 사용할 사용자 반환.
    로그인 미구현: 첫 번째 사용자 사용 (테스트 편의).
    로그인 연동 시 current_user 반환으로 교체.
    """
    try:
        if hasattr(current_app, "login_manager"):
            from flask_login import current_user

            if current_user.is_authenticated:
                return current_user
    except (ImportError, AttributeError, RuntimeError):
        pass
    return User.query.first()


def login_required(f):
    """
    로그인 필수. 미로그인+TESTING 시 그냥 진행 (첫 사용자로 대체).
    Flask-Login 미설정 시에도 진행.
    """

    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            if hasattr(current_app, "login_manager"):
                from flask_login import current_user

                if current_user.is_authenticated:
                    return f(*args, **kwargs)
                if not current_app.config.get("TESTING"):
                    return redirect(url_for("auth.login"))
        except (ImportError, AttributeError, RuntimeError):
            pass
        return f(*args, **kwargs)

    return wrapped


@main_bp.route("/subscriptions")
@login_required
def subscriptions():
    """구독한 채널의 영상만 모아보는 피드. 로그인 필요 (테스트 시 첫 사용자로 대체)."""
    user = _get_subscriptions_user()
    if not user:
        videos = Video.query.filter(Video.id < 0).paginate(page=1, per_page=12)
        return render_template("main/subscriptions.html", videos=videos)

    # 구독 중인 채널 ID 목록
    subscribed_ids = [
        s.subscribed_to_id for s in user.subscriptions_rel.all()
    ]
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    if not subscribed_ids:
        videos = Video.query.filter(Video.id < 0).paginate(page=1, per_page=12)
    else:
        videos = (
            Video.query.options(joinedload(Video.user))
            .filter(Video.user_id.in_(subscribed_ids))
            .order_by(Video.created_at.desc())
            .paginate(page=page, per_page=12)
        )

    return render_template("main/subscriptions.html", videos=videos)


@main_bp.route("/user/<username>/subscribe", methods=["POST"])
def subscribe_toggle(username):
    """구독/구독해제 토글. DB 반영 후 JSON 응답."""
    target = User.query.filter_by(username=username).first_or_404()
    current = _get_subscriptions_user()
    if not current:
        return jsonify({"ok": False, "error": "로그인이 필요합니다."}), 401
    if current.id == target.id:
        return jsonify({"ok": False, "error": "자기 자신은 구독할 수 없습니다."}), 400

    sub = Subscription.query.filter_by(
        subscriber_id=current.id,
        subscribed_to_id=target.id,
    ).first()

    if sub:
        db.session.delete(sub)
        is_subscribed = False
    else:
        db.session.add(Subscription(subscriber_id=current.id, subscribed_to_id=target.id))
        is_subscribed = True
    db.session.commit()
    subscriber_count = target.subscribers_rel.count()

    return jsonify({"ok": True, "is_subscribed": is_subscribed, "subscriber_count": subscriber_count})


@main_bp.route("/tag/<tag_name>")
def tag(tag_name):
    tag_obj = Tag.query.filter_by(name=tag_name).first()
    if tag_obj is None:
        videos = []
        results_count = 0
    else:
        videos = (
            Video.query.options(joinedload(Video.user))
            .join(video_tags)
            .filter(video_tags.c.tag_id == tag_obj.id)
            .order_by(Video.created_at.desc())
            .limit(24)
            .all()
        )
        results_count = tag_obj.videos.count()
    popular_tags = _get_popular_tags()
    return render_template(
        "main/tag.html",
        tag=tag_name,
        videos=videos,
        results_count=results_count,
        popular_tags=popular_tags,
    )


@main_bp.route("/user/<username>")
def user_profile(username):
    """사용자 프로필 – first_or_404, 채널 통계, 비디오 목록(페이지네이션)."""
    user = User.query.filter_by(username=username).first_or_404()

    # 채널 통계 (func.sum, func.count)
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
    stats = {
        "total_views": stats_row.total_views or 0,
        "total_likes": stats_row.total_likes or 0,
        "video_count": stats_row.video_count or 0,
        "subscriber_count": subscriber_count,
    }

    # 비디오 목록 최신순, 페이지네이션
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    videos = (
        Video.query.filter_by(user_id=user.id)
        .order_by(Video.created_at.desc())
        .paginate(page=page, per_page=12)
    )

    current = _get_subscriptions_user()
    is_subscribed = _is_subscribed(current.id if current else None, user.id)
    return render_template(
        "main/profile.html",
        user=user,
        videos=videos,
        stats=stats,
        is_subscribed=is_subscribed,
    )
