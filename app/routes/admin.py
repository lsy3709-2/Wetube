"""관리자 라우트 – DB 실데이터 연동, Flask-Login 인증."""

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app import db
from app.models import Comment, User, Video

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _admin_required(f):
    """관리자 권한 필수. 비로그인 → 로그인, 일반 유저 → 메인으로 리다이렉트 + 에러 메시지."""
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=url_for("admin.index")))
        if not getattr(current_user, "is_admin", False):
            flash("관리자만 접근할 수 있습니다.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return wrapped


@admin_bp.route("/login")
def login():
    return redirect(url_for("auth.login"))


@admin_bp.route("/")
@login_required
@_admin_required
def index():
    """관리자 대시보드 – 통계 + 사용자/비디오/댓글 목록(표 형태, 삭제 버튼)."""
    stats = {
        "user_count": User.query.count(),
        "video_count": Video.query.count(),
        "channel_count": User.query.count(),
        "comment_count": Comment.query.count(),
    }
    # 통합 관리용 목록 (각 최근 20건)
    users_list = User.query.order_by(User.created_at.desc()).limit(20).all()
    videos_list = (
        Video.query.options(joinedload(Video.user))
        .order_by(Video.created_at.desc())
        .limit(20)
        .all()
    )
    comments_list = (
        Comment.query.options(
            joinedload(Comment.user),
            joinedload(Comment.video),
        )
        .order_by(Comment.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "admin/admin.html",
        stats=stats,
        users_list=users_list,
        videos_list=videos_list,
        comments_list=comments_list,
    )


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@_admin_required
def user_edit(user_id):
    """관리자가 회원 정보 수정 (비밀번호·프로필 이미지·닉네임·이메일)."""
    user = User.query.get_or_404(user_id)
    if request.method == "GET":
        return render_template("admin/user_edit.html", edit_user=user)

    # POST
    nickname = (request.form.get("nickname") or "").strip() or None
    email = (request.form.get("email") or "").strip()
    new_password = request.form.get("new_password") or ""
    new_password_confirm = request.form.get("new_password_confirm") or ""

    if not email:
        flash("이메일은 필수입니다.", "error")
        return render_template("admin/user_edit.html", edit_user=user), 400
    existing = User.query.filter(User.email == email, User.id != user.id).first()
    if existing:
        flash(f"이미 사용 중인 이메일입니다: {email}", "error")
        return render_template("admin/user_edit.html", edit_user=user), 400
    if new_password:
        if new_password != new_password_confirm:
            flash("새 비밀번호와 확인이 일치하지 않습니다.", "error")
            return render_template("admin/user_edit.html", edit_user=user), 400
        if len(new_password) < 4:
            flash("새 비밀번호는 4자 이상이어야 합니다.", "error")
            return render_template("admin/user_edit.html", edit_user=user), 400
        user.set_password(new_password)

    profile_file = request.files.get("profile_image")
    if profile_file and profile_file.filename:
        from app.utils.image import validate_image_file
        allowed_ext = current_app.config.get("ALLOWED_PROFILE_IMAGE_EXTENSIONS", {"jpg", "jpeg", "png", "gif", "webp"})
        max_size = current_app.config.get("MAX_PROFILE_IMAGE_SIZE", 5 * 1024 * 1024)
        ok, err_msg = validate_image_file(profile_file, allowed_ext, max_size)
        if not ok:
            flash(err_msg, "error")
            return render_template("admin/user_edit.html", edit_user=user), 400
        try:
            from app.routes.auth import _save_profile_image
            _save_profile_image(profile_file, user)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("admin/user_edit.html", edit_user=user), 400

    user.nickname = nickname
    user.email = email
    db.session.commit()
    flash("회원 정보가 수정되었습니다.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@_admin_required
def user_delete(user_id):
    """관리자 회원 삭제. 본인(admin)은 삭제 불가."""
    if user_id == current_user.id:
        flash("자기 자신은 삭제할 수 없습니다.", "error")
        return redirect(url_for("admin.index"))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("회원이 삭제되었습니다.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/videos/<int:video_id>/delete", methods=["POST"])
@login_required
@_admin_required
def video_delete(video_id):
    """관리자 동영상 삭제."""
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    flash("동영상이 삭제되었습니다.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/users")
@login_required
@_admin_required
def users():
    """회원 관리 – DB users 테이블 연동. q 파라미터로 검색."""
    from sqlalchemy import or_

    page = request.args.get("page", 1, type=int)
    q_param = (request.args.get("q") or "").strip()
    if page < 1:
        page = 1

    query = User.query
    if q_param:
        pattern = f"%{q_param}%"
        query = query.filter(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.nickname.ilike(pattern),
            )
        )
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15
    )
    return render_template("admin/users.html", users=pagination)


@admin_bp.route("/videos")
@login_required
@_admin_required
def videos():
    """동영상 관리 – DB videos 테이블 연동. q 파라미터로 제목/업로더 검색."""
    from sqlalchemy import or_

    page = request.args.get("page", 1, type=int)
    q_param = (request.args.get("q") or "").strip()
    if page < 1:
        page = 1

    query = Video.query.options(joinedload(Video.user))
    if q_param:
        pattern = f"%{q_param}%"
        query = query.join(Video.user).filter(
            or_(
                Video.title.ilike(pattern),
                User.username.ilike(pattern),
            )
        )
    pagination = query.order_by(Video.created_at.desc()).paginate(
        page=page, per_page=15
    )
    return render_template("admin/videos.html", videos=pagination)


@admin_bp.route("/comments")
@login_required
@_admin_required
def comments():
    """댓글 관리 – DB comments 테이블 연동, 검색·페이지네이션."""
    from sqlalchemy import or_

    page = request.args.get("page", 1, type=int)
    q_param = (request.args.get("q") or "").strip()
    if page < 1:
        page = 1

    query = Comment.query.options(
        joinedload(Comment.user),
        joinedload(Comment.video),
    ).order_by(Comment.created_at.desc())

    if q_param:
        pattern = f"%{q_param}%"
        query = query.join(Comment.user).filter(
            or_(
                Comment.content.ilike(pattern),
                User.username.ilike(pattern),
            )
        )

    pagination = query.paginate(page=page, per_page=15)
    return render_template("admin/comments.html", comments=pagination)


@admin_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
@_admin_required
def comment_delete(comment_id):
    """관리자 댓글 삭제. 본인 확인 없이 삭제 가능."""
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("댓글이 삭제되었습니다.", "success")
    if request.form.get("next") == "index":
        return redirect(url_for("admin.index"))
    page = request.form.get("page") or request.args.get("page", 1)
    q = request.form.get("q") or request.args.get("q", "")
    return redirect(url_for("admin.comments", page=page, q=q))


@admin_bp.route("/database")
@login_required
@_admin_required
def database():
    return render_template("admin/database.html")


@admin_bp.route("/api-preview")
@login_required
@_admin_required
def api_preview():
    """REST API 데이터 미리보기 화면. JS에서 /api/videos, /api/tags/popular 호출."""
    return render_template("admin/api_preview.html")


@admin_bp.route("/db-verify")
@login_required
@_admin_required
def db_verify():
    """
    DB 검증 리포트 화면. scripts/db_verify.py 실행 후 생성된 리포트를 표시.
    리포트 없으면 안내 페이지.
    """
    report_path = Path(current_app.instance_path) / "db_verify_report.html"
    if report_path.exists():
        return send_file(str(report_path), mimetype="text/html")
    return render_template("admin/db_verify_placeholder.html")


@admin_bp.route("/query")
@login_required
@_admin_required
def query():
    return render_template("admin/query.html")


@admin_bp.route("/table/<table_name>")
@login_required
@_admin_required
def table_view(table_name):
    # 프론트 전용: 테이블별 구조 및 샘플 데이터
    TABLES = {
        "user": {
            "columns": [
                {"name": "id", "type": "INT", "key": "PK", "null": "NO"},
                {"name": "username", "type": "VARCHAR(50)", "key": "-", "null": "NO"},
                {"name": "email", "type": "VARCHAR(100)", "key": "-", "null": "YES"},
                {"name": "created_at", "type": "DATETIME", "key": "-", "null": "NO"},
            ],
            "sample": [
                {"id": 1, "username": "aaa", "email": "aaa@example.com", "created_at": "2025-01-20"},
                {"id": 2, "username": "admin", "email": "admin@example.com", "created_at": "2025-01-19"},
                {"id": 3, "username": "lsye", "email": "lsye@example.com", "created_at": "2025-01-18"},
            ],
        },
        "video": {
            "columns": [
                {"name": "id", "type": "INT", "key": "PK", "null": "NO"},
                {"name": "title", "type": "VARCHAR(200)", "key": "-", "null": "NO"},
                {"name": "user_id", "type": "INT", "key": "FK", "null": "NO"},
                {"name": "views", "type": "INT", "key": "-", "null": "NO"},
                {"name": "created_at", "type": "DATETIME", "key": "-", "null": "NO"},
            ],
            "sample": [
                {"id": 1, "title": "샘플 동영상 1", "user_id": 1, "views": 100, "created_at": "2025-01-20"},
                {"id": 2, "title": "샘플 동영상 2", "user_id": 2, "views": 200, "created_at": "2025-01-19"},
                {"id": 3, "title": "샘플 동영상 3", "user_id": 3, "views": 150, "created_at": "2025-01-18"},
            ],
        },
        "comment": {
            "columns": [
                {"name": "id", "type": "INT", "key": "PK", "null": "NO"},
                {"name": "content", "type": "TEXT", "key": "-", "null": "NO"},
                {"name": "user_id", "type": "INT", "key": "FK", "null": "NO"},
                {"name": "video_id", "type": "INT", "key": "FK", "null": "NO"},
                {"name": "parent_id", "type": "INT", "key": "FK", "null": "YES"},
                {"name": "created_at", "type": "DATETIME", "key": "-", "null": "NO"},
            ],
            "sample": [],  # DB에서 실제 데이터 로드
        },
        "channel": {
            "columns": [
                {"name": "id", "type": "INT", "key": "PK", "null": "NO"},
                {"name": "user_id", "type": "INT", "key": "FK", "null": "NO"},
                {"name": "name", "type": "VARCHAR(100)", "key": "-", "null": "NO"},
                {"name": "subscribers", "type": "INT", "key": "-", "null": "NO"},
            ],
            "sample": [
                {"id": 1, "user_id": 1, "name": "aaa 채널", "subscribers": 50},
                {"id": 2, "user_id": 3, "name": "lsye 채널", "subscribers": 100},
            ],
        },
        "subscription": {
            "columns": [
                {"name": "id", "type": "INT", "key": "PK", "null": "NO"},
                {"name": "user_id", "type": "INT", "key": "FK", "null": "NO"},
                {"name": "channel_id", "type": "INT", "key": "FK", "null": "NO"},
                {"name": "created_at", "type": "DATETIME", "key": "-", "null": "NO"},
            ],
            "sample": [
                {"id": 1, "user_id": 1, "channel_id": 2, "created_at": "2025-01-20"},
                {"id": 2, "user_id": 2, "channel_id": 1, "created_at": "2025-01-19"},
            ],
        },
    }
    data = TABLES.get(table_name)
    if not data:
        columns = [{"name": "id", "type": "INT", "key": "PK", "null": "NO"}]
        sample_data = []
    else:
        columns = data["columns"]
        sample_data = data["sample"]

    # comment 테이블: DB에서 실제 데이터 로드
    if table_name == "comment":
        comments = Comment.query.order_by(Comment.created_at.desc()).limit(20).all()
        sample_data = [
            {
                "id": c.id,
                "content": (c.content[:50] + "...") if c.content and len(c.content) > 50 else (c.content or ""),
                "user_id": c.user_id,
                "video_id": c.video_id,
                "parent_id": c.parent_id,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
            }
            for c in comments
        ]
    return render_template(
        "admin/table_view.html",
        table_name=table_name,
        columns=columns,
        sample_data=sample_data,
    )
