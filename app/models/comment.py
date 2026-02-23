"""
댓글 모델 – comments 테이블.
parent_id로 대댓글(답글) 구조 지원.
"""

from datetime import datetime, timezone

from app import db


def _utc_now():
    return datetime.now(timezone.utc)


class Comment(db.Model):
    """비디오 댓글 및 대댓글."""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    likes = db.Column(db.Integer, nullable=False, default=0)
    dislikes = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=_utc_now)
    updated_at = db.Column(db.DateTime, default=_utc_now, onupdate=_utc_now)

    user = db.relationship("User", backref=db.backref("comments", lazy="dynamic"))
    video = db.relationship("Video", backref=db.backref("video_comments", lazy="dynamic"))
    parent = db.relationship(
        "Comment",
        remote_side=[id],
        backref=db.backref("replies", lazy="joined", order_by="Comment.created_at"),
        foreign_keys=[parent_id],
    )
