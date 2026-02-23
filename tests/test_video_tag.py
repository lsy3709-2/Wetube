# 단위 테스트 – Video-Tag N:M 관계 및 save_tags
import pytest

from app import db
from app.models import Tag, User, Video


@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (id=1, create_app에서 생성됨)."""
    return db.session.get(User, 1)


@pytest.fixture
def video(app_ctx, user):
    """테스트용 비디오 (태그 없음)."""
    v = Video(title="테스트 동영상", video_path="test.mp4", user_id=user.id)
    db.session.add(v)
    db.session.commit()
    return v


# ----- Tag 모델 -----
def test_tag_model_create(app_ctx):
    """Tag 생성 및 name UNIQUE 저장."""
    tag = Tag(name="Python")
    db.session.add(tag)
    db.session.commit()
    assert tag.id is not None
    assert tag.name == "Python"
    assert tag.created_at is not None


def test_tag_name_unique(app_ctx):
    """동일 name으로 Tag 중복 생성 시 UNIQUE 제약 위반."""
    db.session.add(Tag(name="Flask"))
    db.session.commit()
    db.session.add(Tag(name="Flask"))
    with pytest.raises(Exception):
        db.session.commit()
    db.session.rollback()


# ----- save_tags: 기본 파싱 -----
def test_save_tags_parses_comma_separated(app_ctx, video):
    """콤마로 구분된 문자열 → 여러 Tag로 변환 후 연결."""
    video.save_tags("태그1, 태그2, 태그3")
    names = sorted(t.name for t in video.tags)
    assert names == ["태그1", "태그2", "태그3"]


def test_save_tags_strips_whitespace(app_ctx, video):
    """태그 앞뒤 공백 제거."""
    video.save_tags("  A  ,  B  ,  C  ")
    names = sorted(t.name for t in video.tags)
    assert names == ["A", "B", "C"]


def test_save_tags_empty_string(app_ctx, video):
    """빈 문자열 → 태그 목록 비움."""
    video.save_tags("태그1")
    assert len(video.tags) == 1
    video.save_tags("")
    assert len(video.tags) == 0


def test_save_tags_none(app_ctx, video):
    """None 입력 → 태그 목록 비움."""
    video.save_tags("태그1")
    video.save_tags(None)
    assert len(video.tags) == 0


def test_save_tags_replaces_existing(app_ctx, video):
    """기존 태그는 새 목록으로 교체됨."""
    video.save_tags("이전1, 이전2")
    video.save_tags("새1, 새2")
    names = sorted(t.name for t in video.tags)
    assert names == ["새1", "새2"]


# ----- save_tags: get_or_create -----
def test_save_tags_reuses_existing_tag(app_ctx, video):
    """이미 존재하는 Tag 이름은 재사용 (get_or_create)."""
    tag_a = Tag(name="공유태그")
    db.session.add(tag_a)
    db.session.commit()
    before_count = Tag.query.count()

    video.save_tags("공유태그")
    after_count = Tag.query.count()
    assert after_count == before_count
    assert video.tags[0].name == "공유태그"
    assert video.tags[0].id == tag_a.id


def test_save_tags_creates_new_tags(app_ctx, video):
    """없는 태그는 새로 생성."""
    before_count = Tag.query.count()
    video.save_tags("신규1, 신규2")
    after_count = Tag.query.count()
    assert after_count == before_count + 2


# ----- save_tags: 50자 초과 무시 -----
def test_save_tags_ignores_over_50_chars(app_ctx, video):
    """50자 초과 태그는 무시됨."""
    short = "짧은태그"
    long_tag = "가" * 51
    video.save_tags(f"{short}, {long_tag}")
    names = [t.name for t in video.tags]
    assert names == [short]


# ----- N:M 관계 -----
def test_video_tags_relationship(app_ctx, video):
    """Video.tags ↔ Tag.videos 양방향 관계."""
    video.save_tags("A, B")
    tag_a = Tag.query.filter_by(name="A").first()
    videos_with_a = tag_a.videos.all()
    assert len(videos_with_a) == 1
    assert videos_with_a[0].id == video.id


def test_commit_false(app_ctx, video):
    """commit=False 시 호출자가 직접 commit해야 DB에 반영됨."""
    video.save_tags("태그1, 태그2", commit=False)
    db.session.commit()  # 호출자가 명시적으로 commit
    video_reloaded = db.session.get(Video, video.id)
    assert len(video_reloaded.tags) == 2
