"""
비디오 모델 – videos 테이블.
video_path / thumbnail_path 는 파일명만 저장, 실제 파일은 config 폴더에 저장됨.
Video ↔ Tag N:M 관계 (video_tags 중간 테이블).
"""
from datetime import datetime, timezone

from app import db

# datetime.utcnow() deprecated → datetime.now(timezone.utc) 사용
def _utc_now():
    return datetime.now(timezone.utc)


# Video ↔ Tag N:M 중간 테이블 (table.sql의 video_tags)
video_tags = db.Table(
    "video_tags",
    db.Column("video_id", db.Integer, db.ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=_utc_now),
)

# Video ↔ User N:M 좋아요 중간 테이블 (table.sql의 video_likes)
# 사용자가 좋아요를 누르면 (user_id, video_id) 레코드가 추가됨
video_likes = db.Table(
    "video_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("video_id", db.Integer, db.ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=_utc_now),
)


class Video(db.Model):
    """업로드된 동영상 정보."""

    # 테이블명
    __tablename__ = "videos"

    # ----- 기본 키 -----
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ----- 메타데이터 -----
    title = db.Column(db.String(200), nullable=False)       # 제목 (필수)
    description = db.Column(db.Text, nullable=True)        # 설명 (선택)
    category = db.Column(db.String(50), nullable=True)     # 카테고리 (미사용 가능)
    duration = db.Column(db.Integer, nullable=True)        # 재생 시간(초)

    # ----- 파일 경로/URL (로컬: 파일명, Cloudinary: secure_url) -----
    video_path = db.Column(db.String(500), nullable=False)       # 비디오 파일명(로컬) 또는 public_id
    thumbnail_path = db.Column(db.String(500), nullable=True)    # 썸네일 파일명(로컬)
    video_public_id = db.Column(db.String(255), nullable=True)   # Cloudinary 비디오 public_id (삭제용)
    thumbnail_public_id = db.Column(db.String(255), nullable=True)  # Cloudinary 썸네일 public_id (삭제용)
    video_url = db.Column(db.String(512), nullable=True)         # Cloudinary secure_url (비디오)
    thumbnail_url = db.Column(db.String(512), nullable=True)      # Cloudinary secure_url (썸네일)

    # ----- 통계 -----
    views = db.Column(db.Integer, nullable=False, default=0)   # 조회수
    likes = db.Column(db.Integer, nullable=False, default=0) # 좋아요 수

    # ----- 작성자 (users.id 참조. 유저 삭제 시 해당 영상도 CASCADE 삭제) -----
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = db.relationship("User", backref=db.backref("uploaded_videos", lazy="dynamic"))

    # ----- 타임스탬프 -----
    created_at = db.Column(db.DateTime, default=_utc_now)                    # 업로드 시각
    updated_at = db.Column(db.DateTime, default=_utc_now, onupdate=_utc_now)  # 수정 시 자동 갱신

    # ----- N:M 관계: Tag -----
    tags = db.relationship(
        "Tag",
        secondary=video_tags,
        backref=db.backref("videos", lazy="dynamic"),
        lazy="select",  # save_tags에서 목록 할당을 위해 select 사용
    )

    def get_video_url(self):
        """비디오 재생 URL. Cloudinary URL이 있으면 반환, 없으면 로컬 media 경로."""
        if self.video_url:
            return self.video_url
        from flask import url_for
        return url_for("main.media_video", filename=self.video_path)

    def get_thumbnail_url(self):
        """썸네일 URL. Cloudinary URL이 있으면 반환, 없으면 로컬 media 경로. 없으면 None."""
        if self.thumbnail_url:
            return self.thumbnail_url
        if not self.thumbnail_path:
            return None
        from flask import url_for
        return url_for("main.media_thumbnail", filename=self.thumbnail_path)

    def save_tags(self, tag_string, commit=True):
        """
        콤마로 구분된 태그 문자열을 파싱해 Tag 객체로 변환 후 비디오에 연결.
        예: "태그1, 태그2, 태그3" -> [Tag(태그1), Tag(태그2), Tag(태그3)]
        기존 태그 연결은 새 태그 목록으로 교체됨.
        """
        from app.models.tag import Tag

        if not tag_string or not isinstance(tag_string, str):
            tag_names = []
        else:
            tag_names = [name.strip() for name in tag_string.split(",") if name.strip()]

        tag_objects = []
        for name in tag_names:
            if len(name) > 50:
                continue
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
            tag_objects.append(tag)

        self.tags = tag_objects
        if commit:
            db.session.commit()
