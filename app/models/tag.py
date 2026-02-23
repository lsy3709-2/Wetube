"""
태그 모델 – tags 테이블.
Video와 N:M 관계 (video_tags 중간 테이블).
"""
from datetime import datetime, timezone

from app import db


def _utc_now():
    """datetime.utcnow() deprecated 대체."""
    return datetime.now(timezone.utc)


class Tag(db.Model):
    """태그 정보."""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=_utc_now)
