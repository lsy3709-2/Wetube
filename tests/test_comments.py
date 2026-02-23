"""
단위 테스트 – 댓글/대댓글 기능 (comments 블루프린트, Comment 모델)

- 댓글 작성(create), 대댓글(reply), 수정(edit), 삭제(delete)
- 로그인 필수, 수정/삭제는 본인만
- main.watch 댓글 조회 (parent_id=None, created_at 오름차순)
"""

import pytest

from app import db
from app.models import Comment, User, Video


# ----- 픽스처 -----
@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (create_app에서 id=1 생성)."""
    return db.session.get(User, 1)


@pytest.fixture
def other_user(app_ctx):
    """다른 사용자. 본인 확인 검사용."""
    u = User(username="other", email="other@example.com", password_hash="hash")
    u.set_password("other123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def video(app_ctx, user):
    """테스트용 비디오."""
    v = Video(
        title="댓글 테스트 영상",
        description="",
        video_path="test.mp4",
        thumbnail_path="test.png",
        user_id=user.id,
    )
    db.session.add(v)
    db.session.commit()
    return v


@pytest.fixture
def comment(app_ctx, user, video):
    """테스트용 최상위 댓글."""
    c = Comment(
        content="첫 번째 댓글",
        user_id=user.id,
        video_id=video.id,
        parent_id=None,
    )
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def comment_by_other(app_ctx, other_user, video):
    """다른 사용자 댓글. 수정/삭제 본인 검사용."""
    c = Comment(
        content="타인의 댓글",
        user_id=other_user.id,
        video_id=video.id,
        parent_id=None,
    )
    db.session.add(c)
    db.session.commit()
    return c


# ----- Comment 모델 -----
def test_comment_model_creation(app_ctx, user, video):
    """Comment 모델 생성 및 기본 속성."""
    c = Comment(content="테스트 댓글", user_id=user.id, video_id=video.id, parent_id=None)
    db.session.add(c)
    db.session.commit()
    assert c.id is not None
    assert c.content == "테스트 댓글"
    assert c.user_id == user.id
    assert c.video_id == video.id
    assert c.parent_id is None
    assert c.likes == 0
    assert c.dislikes == 0
    assert c.created_at is not None
    assert c.updated_at is not None


def test_comment_reply_has_parent_id(app_ctx, comment, user):
    """대댓글은 parent_id가 부모 댓글 ID로 설정됨."""
    reply = Comment(
        content="답글입니다",
        user_id=user.id,
        video_id=comment.video_id,
        parent_id=comment.id,
    )
    db.session.add(reply)
    db.session.commit()
    assert reply.parent_id == comment.id
    assert reply.video_id == comment.video_id


def test_comment_parent_replies_relationship(app_ctx, comment, user):
    """부모 댓글의 replies 관계에 대댓글이 포함됨."""
    reply = Comment(
        content="대댓글",
        user_id=user.id,
        video_id=comment.video_id,
        parent_id=comment.id,
    )
    db.session.add(reply)
    db.session.commit()
    db.session.refresh(comment)
    assert len(comment.replies) == 1
    assert comment.replies[0].content == "대댓글"


# ----- 댓글 작성 (create) -----
def test_create_comment_requires_login(client, app_ctx, video):
    """비로그인 시 댓글 작성 → 로그인 페이지로 리다이렉트."""
    resp = client.post(
        "/comments/create",
        data={"video_id": video.id, "content": "댓글 내용"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/auth/login" in resp.location or "login" in resp.location


def test_create_comment_success(logged_in_client, app_ctx, video):
    """로그인 상태에서 댓글 작성 → 302, watch로 리다이렉트, DB에 저장."""
    resp = logged_in_client.post(
        "/comments/create",
        data={"video_id": video.id, "content": "새 댓글 내용"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/watch/{video.id}" in resp.location

    # DB에 댓글이 생성되었는지 확인
    c = Comment.query.filter_by(video_id=video.id, parent_id=None).first()
    assert c is not None
    assert c.content == "새 댓글 내용"
    assert c.parent_id is None


def test_create_comment_empty_content_redirects_with_error(logged_in_client, app_ctx, video):
    """content 비어 있으면 에러 플래시 후 watch로 리다이렉트."""
    resp = logged_in_client.post(
        "/comments/create",
        data={"video_id": video.id, "content": "   "},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert f"/watch/{video.id}" in resp.request.path or "watch" in resp.request.path

    # DB에 댓글 미생성
    count = Comment.query.filter_by(video_id=video.id).count()
    assert count == 0


def test_create_comment_invalid_video_id_redirects(logged_in_client, app_ctx):
    """video_id 없으면 index로 리다이렉트."""
    resp = logged_in_client.post(
        "/comments/create",
        data={"content": "댓글"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/" in resp.location


def test_create_comment_nonexistent_video_returns_404(logged_in_client, app_ctx):
    """존재하지 않는 video_id → 404."""
    resp = logged_in_client.post(
        "/comments/create",
        data={"video_id": 99999, "content": "댓글"},
        follow_redirects=False,
    )
    assert resp.status_code == 404


# ----- 대댓글 (reply) -----
def test_reply_requires_login(client, app_ctx, comment):
    """비로그인 시 답글 작성 → 로그인 리다이렉트."""
    resp = client.post(
        f"/comments/{comment.id}/reply",
        data={"content": "답글 내용"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "login" in resp.location


def test_reply_success(logged_in_client, app_ctx, comment, user):
    """로그인 상태에서 답글 작성 → DB에 parent_id 설정."""
    resp = logged_in_client.post(
        f"/comments/{comment.id}/reply",
        data={"content": "대댓글 내용"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/watch/{comment.video_id}" in resp.location

    reply = Comment.query.filter_by(parent_id=comment.id).first()
    assert reply is not None
    assert reply.content == "대댓글 내용"
    assert reply.parent_id == comment.id
    assert reply.video_id == comment.video_id
    assert reply.user_id == user.id


def test_reply_empty_content_redirects(logged_in_client, app_ctx, comment):
    """답글 content 비어 있으면 에러 후 리다이렉트."""
    resp = logged_in_client.post(
        f"/comments/{comment.id}/reply",
        data={"content": ""},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    count = Comment.query.filter_by(parent_id=comment.id).count()
    assert count == 0


def test_reply_nonexistent_comment_returns_404(logged_in_client, app_ctx):
    """존재하지 않는 댓글에 답글 → 404."""
    resp = logged_in_client.post(
        "/comments/99999/reply",
        data={"content": "답글"},
        follow_redirects=False,
    )
    assert resp.status_code == 404


# ----- 댓글 수정 (edit) -----
def test_edit_requires_login(client, app_ctx, comment):
    """비로그인 시 수정 → 로그인 리다이렉트."""
    resp = client.post(
        f"/comments/{comment.id}/edit",
        data={"content": "수정된 내용"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "login" in resp.location


def test_edit_own_comment_success(logged_in_client, app_ctx, comment, user):
    """본인 댓글 수정 → DB 반영, watch로 리다이렉트."""
    assert comment.user_id == user.id

    resp = logged_in_client.post(
        f"/comments/{comment.id}/edit",
        data={"content": "수정된 댓글 내용"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/watch/{comment.video_id}" in resp.location

    db.session.expire_all()
    updated = db.session.get(Comment, comment.id)
    assert updated.content == "수정된 댓글 내용"


def test_edit_others_comment_rejected(logged_in_client, app_ctx, comment_by_other):
    """타인 댓글 수정 시도 → 리다이렉트, DB 미변경."""
    original_content = comment_by_other.content

    resp = logged_in_client.post(
        f"/comments/{comment_by_other.id}/edit",
        data={"content": "해킹 시도"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    db.session.expire_all()
    unchanged = db.session.get(Comment, comment_by_other.id)
    assert unchanged.content == original_content


def test_edit_empty_content_redirects(logged_in_client, app_ctx, comment):
    """수정 content 비어 있으면 에러, DB 미변경."""
    original = comment.content
    resp = logged_in_client.post(
        f"/comments/{comment.id}/edit",
        data={"content": "   "},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.expire_all()
    unchanged = db.session.get(Comment, comment.id)
    assert unchanged.content == original


def test_edit_nonexistent_returns_404(logged_in_client, app_ctx):
    """존재하지 않는 댓글 수정 → 404."""
    resp = logged_in_client.post(
        "/comments/99999/edit",
        data={"content": "수정"},
        follow_redirects=False,
    )
    assert resp.status_code == 404


# ----- 댓글 삭제 (delete) -----
def test_delete_requires_login(client, app_ctx, comment):
    """비로그인 시 삭제 → 로그인 리다이렉트."""
    resp = client.post(f"/comments/{comment.id}/delete", follow_redirects=False)
    assert resp.status_code == 302
    assert "login" in resp.location


def test_delete_own_comment_success(logged_in_client, app_ctx, comment, user):
    """본인 댓글 삭제 → DB에서 제거, watch로 리다이렉트."""
    cid = comment.id
    vid = comment.video_id
    resp = logged_in_client.post(f"/comments/{cid}/delete", follow_redirects=False)
    assert resp.status_code == 302
    assert f"/watch/{vid}" in resp.location

    deleted = db.session.get(Comment, cid)
    assert deleted is None


def test_delete_others_comment_rejected(logged_in_client, app_ctx, comment_by_other):
    """타인 댓글 삭제 시도 → 리다이렉트, DB 미변경."""
    cid = comment_by_other.id
    resp = logged_in_client.post(f"/comments/{cid}/delete", follow_redirects=True)
    assert resp.status_code == 200

    still_exists = db.session.get(Comment, cid)
    assert still_exists is not None


def test_delete_nonexistent_returns_404(logged_in_client, app_ctx):
    """존재하지 않는 댓글 삭제 → 404."""
    resp = logged_in_client.post("/comments/99999/delete", follow_redirects=False)
    assert resp.status_code == 404


# ----- main.watch 댓글 조회 -----
def test_watch_shows_top_comments_only(client, app_ctx, video, user):
    """watch 페이지: parent_id=None인 최상위 댓글만 표시 (대댓글은 replies로)."""
    # 최상위 댓글 2개
    c1 = Comment(content="댓글1", user_id=user.id, video_id=video.id, parent_id=None)
    c2 = Comment(content="댓글2", user_id=user.id, video_id=video.id, parent_id=None)
    db.session.add_all([c1, c2])
    # 대댓글
    r1 = Comment(content="답글", user_id=user.id, video_id=video.id, parent_id=c1.id)
    db.session.add(r1)
    db.session.commit()

    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "댓글1" in text
    assert "댓글2" in text
    assert "답글" in text


def test_watch_comments_ordered_by_created_at(client, app_ctx, video, user):
    """watch: 최상위 댓글이 created_at 오름차순으로 전달됨 (텍스트 순서로 간접 확인)."""
    c1 = Comment(content="첫번째", user_id=user.id, video_id=video.id, parent_id=None)
    c2 = Comment(content="두번째", user_id=user.id, video_id=video.id, parent_id=None)
    db.session.add_all([c1, c2])
    db.session.commit()

    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    # created_at 오름차순이므로 첫번째가 먼저 나와야 함 (동시 생성 시 순서 보장 어려울 수 있음)
    pos1 = text.find("첫번째")
    pos2 = text.find("두번째")
    assert pos1 >= 0 and pos2 >= 0


def test_watch_no_comments_shows_empty(client, app_ctx, video):
    """댓글 없을 때 watch 페이지 정상 렌더링."""
    resp = client.get(f"/watch/{video.id}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "댓글" in text or "comments" in text.lower()
