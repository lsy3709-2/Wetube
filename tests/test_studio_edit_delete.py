# 단위 테스트 – Studio 비디오 수정(Edit) / 삭제(Delete) 라우트

import pytest

from app import db
from app.models import User, Video


@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (create_app에서 id=1 생성)."""
    return db.session.get(User, 1)


@pytest.fixture
def video(app_ctx, user):
    """테스트용 비디오 (수정/삭제 대상)."""
    v = Video(
        title="원본 제목",
        description="원본 설명",
        video_path="test_video.mp4",
        thumbnail_path="test_thumb.png",
        user_id=user.id,
    )
    db.session.add(v)
    db.session.commit()
    return v


@pytest.fixture
def video_title_test(app_ctx, user):
    """제목이 'test'인 비디오 (수정 전 상태 시뮬레이션)."""
    v = Video(
        title="test",
        description="수정 전 설명",
        category="entertainment",
        video_path="sample.mp4",
        thumbnail_path="sample.png",
        user_id=user.id,
    )
    db.session.add(v)
    db.session.commit()
    return v


@pytest.fixture
def other_user(app_ctx):
    """다른 사용자 (id=2). 소유자 검사 403 테스트용."""
    u = User(username="other", email="other@example.com", password_hash="")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def video_other_owner(app_ctx, other_user):
    """다른 사용자 소유 비디오. 수정/삭제 시 403 기대."""
    v = Video(
        title="다른 유저 영상",
        description="",
        video_path="other.mp4",
        user_id=other_user.id,
    )
    db.session.add(v)
    db.session.commit()
    return v


# ----- 수정(Edit) GET -----
def test_edit_get_returns_200_and_form(logged_in_client, app_ctx, video):
    """GET /studio/edit/<id> → 200, 응답에 기존 제목·설명 포함."""
    resp = logged_in_client.get(f"/studio/edit/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "원본 제목" in text
    assert "원본 설명" in text


def test_edit_get_404_for_nonexistent(logged_in_client):
    """존재하지 않는 비디오 ID → 404."""
    resp = logged_in_client.get("/studio/edit/99999")
    assert resp.status_code == 404


def test_edit_get_403_for_other_owner(logged_in_client, app_ctx, video_other_owner):
    """다른 사용자 소유 동영상 수정 페이지 접근 → 403 (소유자만 허용)."""
    resp = logged_in_client.get(f"/studio/edit/{video_other_owner.id}")
    assert resp.status_code == 403


# ----- 수정(Edit) POST (성공) -----
def test_edit_title_changes_and_persists_to_database(logged_in_client, app_ctx, video_title_test):
    """수정 요청 시 제목이 바뀌고, DB에 반영되는지 검증."""
    v = video_title_test
    assert v.title == "test"

    new_title = "변경된 제목"
    resp = logged_in_client.post(
        f"/studio/edit/{v.id}",
        data={
            "title": new_title,
            "description": "설명",
            "category": "",
            "tags": "",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302, "수정 후 리다이렉트되어야 함"

    # DB에서 다시 조회해 반영 여부 확인 (세션 캐시 우회)
    db.session.expire_all()  # 세션 캐시 비우기
    persisted = db.session.get(Video, v.id)
    assert persisted is not None
    assert persisted.title == new_title, "제목이 DB에 반영되어야 함"
    assert persisted.title != "test", "기존 제목이 남아 있으면 안 됨"


def test_edit_title_from_test_to_test_modified(logged_in_client, app_ctx, video_title_test):
    """제목 'test' → 'test 수정'으로 변경 후 DB에 반영되는지 검증."""
    v = video_title_test
    assert v.title == "test"

    new_title = "test 수정"
    resp = logged_in_client.post(
        f"/studio/edit/{v.id}",
        data={
            "title": new_title,
            "description": v.description or "",
            "category": v.category or "",
            "tags": "",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/watch/{v.id}" in resp.location

    db.session.expire_all()
    persisted = db.session.get(Video, v.id)
    assert persisted is not None
    assert persisted.title == "test 수정"
    assert persisted.title != "test"


def test_edit_post_valid_redirects_to_watch(logged_in_client, app_ctx, video):
    """유효한 수정 제출 → 302, Location이 /watch/<id>, DB에 제목·설명 반영."""
    resp = logged_in_client.post(
        f"/studio/edit/{video.id}",
        data={
            "title": "수정된 제목",
            "description": "수정된 설명",
            "category": "education",
            "tags": "A, B",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/watch/{video.id}" in resp.location

    updated = db.session.get(Video, video.id)
    assert updated is not None
    assert updated.title == "수정된 제목"
    assert updated.description == "수정된 설명"
    assert updated.category == "education"


def test_edit_video_with_title_test_updates_db(logged_in_client, app_ctx, video_title_test):
    """제목 'test'인 비디오 수정 → DB에 수정된 데이터만 반영 (제목·설명·카테고리·태그)."""
    v = video_title_test
    assert v.title == "test"
    assert v.description == "수정 전 설명"
    assert v.category == "entertainment"

    resp = logged_in_client.post(
        f"/studio/edit/{v.id}",
        data={
            "title": "수정된 test 제목",
            "description": "수정된 설명입니다.",
            "category": "education",
            "tags": "단위테스트, Flask",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/watch/{v.id}" in resp.location

    # 수정한 데이터가 DB에 반영되었는지 검증
    updated = db.session.get(Video, v.id)
    assert updated is not None
    assert updated.title == "수정된 test 제목"
    assert updated.description == "수정된 설명입니다."
    assert updated.category == "education"
    tag_names = sorted(t.name for t in updated.tags)
    assert tag_names == ["Flask", "단위테스트"]
    # 수정되지 않은 필드는 그대로
    assert updated.video_path == "sample.mp4"
    assert updated.thumbnail_path == "sample.png"
    assert updated.user_id == v.user_id


def test_edit_post_updates_tags(logged_in_client, app_ctx, video):
    """수정 시 태그 문자열 반영 (save_tags)."""
    resp = logged_in_client.post(
        f"/studio/edit/{video.id}",
        data={
            "title": "제목 유지",
            "description": "",
            "category": "",
            "tags": "Python, Flask, 테스트",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302

    updated = db.session.get(Video, video.id)
    tag_names = sorted(t.name for t in updated.tags)
    assert tag_names == ["Flask", "Python", "테스트"]


# ----- 수정(Edit) POST (검증 실패) -----
def test_edit_post_empty_title_returns_400(logged_in_client, app_ctx, video):
    """제목 비어 있으면 400, DB 미변경."""
    resp = logged_in_client.post(
        f"/studio/edit/{video.id}",
        data={"title": "", "description": "설명", "category": "", "tags": ""},
    )
    assert resp.status_code == 400
    text = resp.data.decode("utf-8")
    assert "제목을 입력해주세요" in text or "제목" in text

    unchanged = db.session.get(Video, video.id)
    assert unchanged.title == "원본 제목"


def test_edit_post_title_too_long_returns_400(logged_in_client, app_ctx, video):
    """제목 200자 초과 → 400."""
    resp = logged_in_client.post(
        f"/studio/edit/{video.id}",
        data={
            "title": "가" * 201,
            "description": "",
            "category": "",
            "tags": "",
        },
    )
    assert resp.status_code == 400

    unchanged = db.session.get(Video, video.id)
    assert unchanged.title == "원본 제목"


# ----- 삭제(Delete) POST -----
def test_delete_post_removes_record_redirects_to_studio(logged_in_client, app_ctx, video):
    """POST 삭제 → 302 to /studio/, DB에서 레코드 제거."""
    vid = video.id
    resp = logged_in_client.post(f"/studio/delete/{vid}", follow_redirects=False)
    assert resp.status_code == 302
    assert "/studio" in resp.location

    deleted = db.session.get(Video, vid)
    assert deleted is None


def test_delete_post_404_for_nonexistent(logged_in_client):
    """존재하지 않는 비디오 삭제 요청 → 404."""
    resp = logged_in_client.post("/studio/delete/99999")
    assert resp.status_code == 404


def test_delete_post_403_for_other_owner(logged_in_client, app_ctx, video_other_owner):
    """다른 사용자 소유 동영상 삭제 요청 → 403."""
    resp = logged_in_client.post(f"/studio/delete/{video_other_owner.id}")
    assert resp.status_code == 403


def test_delete_post_file_missing_no_error(logged_in_client, app_ctx, user):
    """파일이 없어도 DB 삭제는 성공 (고아 파일 방지)."""
    v = Video(
        title="고아파일테스트",
        description="",
        video_path="nonexistent_video.mp4",
        thumbnail_path="nonexistent_thumb.png",
        user_id=user.id,
    )
    db.session.add(v)
    db.session.commit()
    vid = v.id
    resp = logged_in_client.post(f"/studio/delete/{vid}", follow_redirects=False)
    assert resp.status_code == 302

    deleted = db.session.get(Video, vid)
    assert deleted is None
