"""
구독 모델 – subscriptions 테이블.
subscriber_id: 구독하는 사용자, subscribed_to_id: 구독 대상 채널.
"""
from datetime import datetime, timezone

from app import db


def _utc_now():
    return datetime.now(timezone.utc)


class Subscription(db.Model):
    """구독 관계: subscriber_id가 subscribed_to_id 채널을 구독."""

    __tablename__ = "subscriptions"

    subscriber_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    subscribed_to_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=_utc_now)
