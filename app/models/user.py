"""
사용자 모델 – users 테이블 (Video FK용).
Flask-Login UserMixin, 비밀번호 해싱 지원.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def _utc_now():
    """datetime.utcnow() deprecated 대체."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """사용자 – Flask-Login 연동, 비밀번호 해싱."""

    __tablename__ = "users"

    # ----- 기본 키 -----
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ----- 계정·프로필 -----
    username = db.Column(db.String(80), nullable=False, unique=True)  # 로그인 ID, 중복 불가
    email = db.Column(db.String(120), nullable=False, unique=True)      # 이메일, 중복 불가
    password_hash = db.Column(db.String(255), nullable=False)          # 비밀번호 해시 (평문 저장 금지)
    nickname = db.Column(db.String(80), nullable=True)                # 표시용 닉네임
    profile_image = db.Column(db.String(255), nullable=True)           # 프로필 이미지 파일 경로 또는 URL
    profile_image_public_id = db.Column(db.String(255), nullable=True) # 클라우드 저장 시 public_id (예: Cloudinary)

    # ----- 권한 -----
    is_admin = db.Column(db.Boolean, nullable=False, default=False)   # 관리자 여부

    # ----- 타임스탬프 -----
    created_at = db.Column(db.DateTime, default=_utc_now)                    # 최초 생성 시각
    updated_at = db.Column(db.DateTime, default=_utc_now, onupdate=_utc_now)  # 수정 시 자동 갱신

    # ----- 구독 관계 -----
    subscriptions_rel = db.relationship(
        "Subscription",
        foreign_keys="Subscription.subscriber_id",
        backref=db.backref("subscriber", lazy="joined"),
        lazy="dynamic",
    )
    subscribers_rel = db.relationship(
        "Subscription",
        foreign_keys="Subscription.subscribed_to_id",
        backref=db.backref("channel", lazy="joined"),
        lazy="dynamic",
    )

    def set_password(self, password):
        """비밀번호를 안전하게 해싱하여 password_hash에 저장."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """입력한 비밀번호가 저장된 해시와 일치하는지 검증."""
        return check_password_hash(self.password_hash, password)

    def get_profile_image_url(self):
        """
        프로필 이미지 URL 반환.
        - Cloudinary: profile_image에 저장된 전체 URL 그대로 반환
        - 로컬: main.media_profile 경로 반환
        """
        if not self.profile_image:
            return None
        from flask import url_for

        # Cloudinary URL(전체 URL)이면 그대로 반환
        if self.profile_image.startswith(("http://", "https://")):
            return self.profile_image
        return url_for("main.media_profile", filename=self.profile_image)
