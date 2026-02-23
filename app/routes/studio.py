# Studio 라우트 – 동영상 관리·업로드 (로컬 또는 Cloudinary)

import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models import Video

studio_bp = Blueprint("studio", __name__, url_prefix="/studio")


def _current_user_id():
    """로그인한 사용자 ID. 미로그인 시 config 기본값 (폴백)."""
    if current_user.is_authenticated:
        return current_user.id
    return current_app.config.get("DEFAULT_USER_ID", 1)


def _require_video_owner(video):
    """동영상 소유자 또는 관리자만 접근 허용. 아니면 403."""
    if video.user_id == _current_user_id():
        return
    from flask_login import current_user

    if current_user.is_authenticated and current_user.is_admin:
        return
    abort(403)


def _get_studio_stats(user_id):
    """
    로그인한 사용자의 총 조회수 합계와 영상 개수를 DB 집계로 반환.
    반환: (total_views, video_count). 데이터 없으면 (0, 0).
    """
    row = (
        db.session.query(
            func.coalesce(func.sum(Video.views), 0).label("total_views"),
            func.count(Video.id).label("video_count"),
        )
        .filter(Video.user_id == user_id)
        .first()
    )
    if row is None:
        return 0, 0
    total_views = int(row.total_views) if row.total_views is not None else 0
    video_count = int(row.video_count) if row.video_count is not None else 0
    return total_views, video_count


def _get_studio_dashboard_data(user_id):
    """
    스튜디오 대시보드용 통계·최근 활동·인기 영상 데이터 반환.
    반환: dict (stats, recent_7d, recent_30d, top_videos)
    """
    row = (
        db.session.query(
            func.count(Video.id).label("video_count"),
            func.coalesce(func.sum(Video.views), 0).label("total_views"),
            func.coalesce(func.sum(Video.likes), 0).label("total_likes"),
        )
        .filter(Video.user_id == user_id)
        .first()
    )
    video_count = int(row.video_count or 0)
    total_views = int(row.total_views or 0)
    total_likes = int(row.total_likes or 0)
    total_comments = 0
    try:
        from sqlalchemy import text

        r = db.session.execute(
            text(
                "SELECT COUNT(*) FROM comments c "
                "INNER JOIN videos v ON c.video_id = v.id WHERE v.user_id = :uid"
            ),
            {"uid": user_id},
        ).scalar()
        total_comments = int(r or 0)
    except Exception:
        pass
    avg_views = round(total_views / video_count, 1) if video_count else 0
    avg_likes = round(total_likes / video_count, 1) if video_count else 0.0

    stats = {
        "video_count": video_count,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "avg_views": avg_views,
        "avg_likes": avg_likes,
    }

    now = datetime.now(timezone.utc)
    since_7d = now - timedelta(days=7)
    since_30d = now - timedelta(days=30)

    def _recent(since):
        r = (
            db.session.query(
                func.count(Video.id).label("cnt"),
                func.coalesce(func.sum(Video.views), 0).label("views"),
                func.coalesce(func.sum(Video.likes), 0).label("likes"),
            )
            .filter(Video.user_id == user_id, Video.created_at >= since)
            .first()
        )
        return {
            "video_count": int(r.cnt or 0),
            "views": int(r.views or 0),
            "likes": int(r.likes or 0),
        }

    recent_7d = _recent(since_7d)
    recent_30d = _recent(since_30d)

    top_videos = (
        Video.query.filter_by(user_id=user_id)
        .order_by(Video.views.desc())
        .limit(5)
        .all()
    )

    return {
        "stats": stats,
        "recent_7d": recent_7d,
        "recent_30d": recent_30d,
        "top_videos": top_videos,
    }


def _allowed_file(filename, allowed_extensions):
    """파일 확장자가 허용 목록에 있는지 검사 (빈 filename·None 처리)."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in allowed_extensions


def _is_cloudinary_enabled():
    """Cloudinary 환경변수 설정 여부."""
    return bool(
        os.environ.get("CLOUDINARY_CLOUD_NAME")
        and os.environ.get("CLOUDINARY_API_KEY")
        and os.environ.get("CLOUDINARY_API_SECRET")
    )


def _save_upload_file(file_storage, save_dir, allowed_extensions, max_size):
    """
    업로드 파일 검증 후 저장.
    반환: (저장된 파일명, None) 또는 (None, 에러메시지)
    """
    if not file_storage or not file_storage.filename:
        return None, "파일이 선택되지 않았습니다."

    filename = file_storage.filename
    if not _allowed_file(filename, allowed_extensions):
        return None, f"허용되지 않는 파일 형식입니다. 허용: {', '.join(sorted(allowed_extensions))}"

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > max_size:
        max_mb = max_size // (1024 * 1024)
        return None, f"파일 크기가 너무 큽니다. 최대 {max_mb}MB까지 업로드할 수 있습니다."

    ext = filename.rsplit(".", 1)[-1].lower()
    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(save_dir, safe_filename)
    try:
        file_storage.save(save_path)
    except OSError as e:
        return None, f"파일 저장 중 오류가 발생했습니다: {e}"
    return safe_filename, None


@studio_bp.route("/")
@studio_bp.route("")  # /studio (끝 슬래시 없음)도 처리
@login_required
def index():
    user_id = _current_user_id()
    videos = Video.query.filter_by(user_id=user_id).order_by(Video.created_at.desc()).all()
    dashboard = _get_studio_dashboard_data(user_id)
    return render_template(
        "studio/index.html",
        videos=videos,
        stats=dashboard["stats"],
        recent_7d=dashboard["recent_7d"],
        recent_30d=dashboard["recent_30d"],
        top_videos=dashboard["top_videos"],
    )


@studio_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "GET":
        return render_template("studio/upload.html")

    # POST: 폼 데이터 수신
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    category_input = (request.form.get("category") or "").strip() or None
    video_file = request.files.get("video")
    thumbnail_file = request.files.get("thumbnail")

    tags_input = (request.form.get("tags") or "").strip()

    # 제목 필수
    if not title:
        flash("제목을 입력해주세요.", "error")
        return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400

    if len(title) > 200:
        flash("제목은 200자 이하여야 합니다.", "error")
        return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400

    # 비디오 파일 검증
    allowed_video = current_app.config["ALLOWED_VIDEO_EXTENSIONS"]
    max_video_size = current_app.config["MAX_VIDEO_SIZE"]
    if not video_file or not video_file.filename:
        flash("동영상 파일을 선택해주세요.", "error")
        return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400
    if not _allowed_file(video_file.filename, allowed_video):
        flash(f"허용되지 않는 동영상 형식입니다. 허용: {', '.join(sorted(allowed_video))}", "error")
        return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400
    video_file.seek(0, os.SEEK_END)
    video_size = video_file.tell()
    video_file.seek(0)
    if video_size > max_video_size:
        flash(f"동영상 크기는 최대 {max_video_size // (1024*1024)}MB까지 가능합니다.", "error")
        return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400

    # 비디오 업로드: Cloudinary 또는 로컬
    video_folder = current_app.config["VIDEO_FOLDER"]
    video_url = None
    video_public_id = None
    video_filename = None

    if _is_cloudinary_enabled():
        from app.utils.cloudinary_upload import upload_video
        video_url, video_public_id, video_err = upload_video(video_file)
        if video_err:
            flash(video_err, "error")
            return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400
        video_filename = video_public_id or "cloud"
    else:
        video_filename, video_error = _save_upload_file(
            video_file, video_folder, allowed_video, max_video_size
        )
        if video_error:
            flash(video_error, "error")
            return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400

    # 썸네일(선택) 업로드: Cloudinary 또는 로컬
    thumbnail_url = None
    thumbnail_public_id = None
    thumbnail_filename = None
    if thumbnail_file and thumbnail_file.filename:
        thumb_folder = current_app.config["THUMBNAIL_FOLDER"]
        allowed_thumb = current_app.config["ALLOWED_THUMBNAIL_EXTENSIONS"]
        max_thumb_size = current_app.config["MAX_THUMBNAIL_SIZE"]
        if not _allowed_file(thumbnail_file.filename, allowed_thumb):
            if not _is_cloudinary_enabled():
                try:
                    if video_filename and not video_url:
                        os.remove(os.path.join(video_folder, video_filename))
                except OSError:
                    pass
            flash(f"허용되지 않는 썸네일 형식입니다. 허용: {', '.join(sorted(allowed_thumb))}", "error")
            return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400

        if _is_cloudinary_enabled():
            from app.utils.cloudinary_upload import upload_image
            thumbnail_url, thumbnail_public_id, thumb_err = upload_image(thumbnail_file)
            if thumb_err:
                if video_public_id:
                    from app.utils.cloudinary_upload import delete_cloudinary_resource
                    delete_cloudinary_resource(video_public_id, "video")
                flash(thumb_err, "error")
                return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400
            thumbnail_filename = thumbnail_public_id or "cloud"
        else:
            thumbnail_filename, thumb_error = _save_upload_file(
                thumbnail_file, thumb_folder, allowed_thumb, max_thumb_size
            )
            if thumb_error:
                try:
                    os.remove(os.path.join(video_folder, video_filename))
                except OSError:
                    pass
                flash(thumb_error, "error")
                return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 400

    # DB에 Video 저장
    user_id = _current_user_id()
    try:
        video = Video(
            title=title,
            description=description or None,
            category=category_input,
            video_path=video_filename,
            thumbnail_path=thumbnail_filename,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            video_public_id=video_public_id,
            thumbnail_public_id=thumbnail_public_id,
            user_id=user_id,
        )
        db.session.add(video)
        db.session.commit()
        if tags_input:
            video.save_tags(tags_input, commit=True)
    except Exception as e:
        db.session.rollback()
        # 저장된 리소스 정리 (Cloudinary 또는 로컬)
        if _is_cloudinary_enabled() and video_public_id:
            from app.utils.cloudinary_upload import delete_cloudinary_resource
            delete_cloudinary_resource(video_public_id, "video")
            if thumbnail_public_id:
                delete_cloudinary_resource(thumbnail_public_id, "image")
        else:
            try:
                os.remove(os.path.join(video_folder, video_filename))
            except OSError:
                pass
            if thumbnail_filename:
                try:
                    os.remove(os.path.join(current_app.config["THUMBNAIL_FOLDER"], thumbnail_filename))
                except OSError:
                    pass
        flash(f"DB 저장 중 오류가 발생했습니다: {e}", "error")
        return render_template("studio/upload.html", title=title, description=description, category=category_input, tags=tags_input), 500

    flash("동영상이 업로드되었습니다.", "success")
    return redirect(url_for("studio.index"))


@studio_bp.route("/edit/<int:video_id>", methods=["GET", "POST"])
@login_required
def edit(video_id):
    video = Video.query.get_or_404(video_id)
    _require_video_owner(video)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        category = (request.form.get("category") or "").strip() or None
        tags_str = (request.form.get("tags") or "").strip()
        current_app.logger.info("studio.edit POST video_id=%s title=%r", video_id, title)
        if not title:
            flash("제목을 입력해주세요.", "error")
            return render_template("studio/edit.html", video=video), 400
        if len(title) > 200:
            flash("제목은 200자 이하여야 합니다.", "error")
            return render_template("studio/edit.html", video=video), 400
        video.title = title
        video.description = description or None
        video.category = category
        video.save_tags(tags_str, commit=False)
        db.session.flush()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("studio.edit commit 실패 video_id=%s: %s", video_id, e)
            flash(f"저장 중 오류가 발생했습니다: {e}", "error")
            return render_template("studio/edit.html", video=video), 500
        current_app.logger.info("studio.edit committed video_id=%s new_title=%r", video_id, title)
        flash("동영상 정보가 수정되었습니다.", "success")
        return redirect(url_for("main.watch", video_id=video_id))
    return render_template("studio/edit.html", video=video)


@studio_bp.route("/delete/<int:video_id>", methods=["POST"])
@login_required
def delete(video_id):
    """
    동영상 삭제: DB 레코드 먼저 삭제 후, 성공 시 uploads/ 내 실제 파일 삭제.
    파일이 없어도 DB 삭제는 완료 (고아 파일 방지).
    로그인 미구현: 소유자(DEFAULT_USER_ID)만 삭제 가능.
    """
    video = Video.query.get_or_404(video_id)
    _require_video_owner(video)
    video_path = video.video_path
    thumbnail_path = video.thumbnail_path
    video_pid = video.video_public_id
    thumb_pid = video.thumbnail_public_id

    db.session.delete(video)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"삭제 중 오류가 발생했습니다: {e}", "error")
        return redirect(url_for("studio.edit", video_id=video_id))

    # DB 삭제 성공 후 리소스 삭제: Cloudinary 또는 로컬
    if _is_cloudinary_enabled() and (video_pid or thumb_pid):
        from app.utils.cloudinary_upload import delete_cloudinary_resource
        if video_pid:
            delete_cloudinary_resource(video_pid, "video")
        if thumb_pid:
            delete_cloudinary_resource(thumb_pid, "image")
    else:
        video_folder = current_app.config["VIDEO_FOLDER"]
        thumb_folder = current_app.config["THUMBNAIL_FOLDER"]
        if video_path:
            try:
                os.remove(os.path.join(video_folder, video_path))
            except OSError:
                pass
        if thumbnail_path:
            try:
                os.remove(os.path.join(thumb_folder, thumbnail_path))
            except OSError:
                pass

    flash("동영상이 삭제되었습니다.", "success")
    return redirect(url_for("studio.index"))
