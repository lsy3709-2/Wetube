"""
댓글 블루프린트 – 비디오 댓글·대댓글 CRUD.
작성/수정/삭제는 모두 로그인 필요, 수정/삭제는 본인만 가능.
"""

from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Comment, Video

comments_bp = Blueprint("comments", __name__, url_prefix="/comments")


def _get_watch_url(video_id):
    """비디오 시청 페이지 URL 반환."""
    return url_for("main.watch", video_id=video_id)


# ----- 댓글 작성 (최상위 댓글) -----
@comments_bp.route("/create", methods=["POST"])
@login_required
def create():
    """최상위 댓글 작성. video_id, content 필요."""
    video_id = request.form.get("video_id", type=int)
    content = (request.form.get("content") or "").strip()

    if not video_id:
        flash("비디오 정보가 없습니다.", "error")
        return redirect(url_for("main.index"))

    video = Video.query.get_or_404(video_id)
    if not content:
        flash("댓글 내용을 입력해주세요.", "error")
        return redirect(_get_watch_url(video_id))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        video_id=video_id,
        parent_id=None,
    )
    db.session.add(comment)
    db.session.commit()
    flash("댓글이 등록되었습니다.", "success")
    return redirect(_get_watch_url(video_id))


# ----- 대댓글 작성 -----
@comments_bp.route("/<int:comment_id>/reply", methods=["POST"])
@login_required
def reply(comment_id):
    """특정 댓글에 대한 대댓글 작성."""
    parent = Comment.query.get_or_404(comment_id)
    content = (request.form.get("content") or "").strip()

    if not content:
        flash("답글 내용을 입력해주세요.", "error")
        return redirect(_get_watch_url(parent.video_id))

    reply_comment = Comment(
        content=content,
        user_id=current_user.id,
        video_id=parent.video_id,
        parent_id=parent.id,
    )
    db.session.add(reply_comment)
    db.session.commit()
    flash("답글이 등록되었습니다.", "success")
    return redirect(_get_watch_url(parent.video_id))


# ----- 댓글 수정 -----
@comments_bp.route("/<int:comment_id>/edit", methods=["POST"])
@login_required
def edit(comment_id):
    """댓글 수정. 본인 댓글만 가능."""
    comment = Comment.query.get_or_404(comment_id)

    if current_user.id != comment.user_id:
        flash("본인의 댓글만 수정할 수 있습니다.", "error")
        return redirect(_get_watch_url(comment.video_id))

    content = (request.form.get("content") or "").strip()
    if not content:
        flash("댓글 내용을 입력해주세요.", "error")
        return redirect(_get_watch_url(comment.video_id))

    comment.content = content
    db.session.commit()
    flash("댓글이 수정되었습니다.", "success")
    return redirect(_get_watch_url(comment.video_id))


# ----- 댓글 삭제 -----
@comments_bp.route("/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete(comment_id):
    """댓글 삭제. 본인 댓글만 가능."""
    comment = Comment.query.get_or_404(comment_id)

    if current_user.id != comment.user_id:
        flash("본인의 댓글만 삭제할 수 있습니다.", "error")
        return redirect(_get_watch_url(comment.video_id))

    video_id = comment.video_id
    db.session.delete(comment)
    db.session.commit()
    flash("댓글이 삭제되었습니다.", "success")
    return redirect(_get_watch_url(video_id))
