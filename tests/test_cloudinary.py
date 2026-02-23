# 단위 테스트 – Cloudinary 업로드·Video URL·프로필 이미지

import os
from pathlib import Path
from io import BytesIO
from unittest.mock import patch

import pytest
from werkzeug.datastructures import FileStorage

from app import db
from app.models import User, Video
from app.utils.cloudinary_upload import (
    delete_cloudinary_resource,
    upload_image,
    upload_video,
)

# uploads 샘플 파일 경로 (프로젝트 루트 기준)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOADS_SAMPLE_VIDEO = PROJECT_ROOT / "uploads" / "videos" / "sample.mp4"
UPLOADS_SAMPLE_THUMB = PROJECT_ROOT / "uploads" / "thumbnails" / "sample.png"
UPLOADS_SAMPLE_PROFILE = PROJECT_ROOT / "uploads" / "profiles" / "sample.jpg"


# ----- Cloudinary 헬퍼: 설정 없을 때 -----
def test_upload_video_returns_error_when_not_configured():
    """Cloudinary 미설정 시 upload_video → 에러 메시지 반환."""
    prev = {}
    for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
        prev[key] = os.environ.pop(key, None)
    try:
        fs = FileStorage(stream=BytesIO(b"fake"), filename="test.mp4", content_type="video/mp4")
        url, pid, err = upload_video(fs)
        assert url is None
        assert pid is None
        assert err is not None
        assert "Cloudinary" in err or "설정" in err
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v


def test_upload_image_returns_error_when_not_configured():
    """Cloudinary 미설정 시 upload_image → 에러 메시지 반환."""
    prev = {}
    for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
        prev[key] = os.environ.pop(key, None)
    try:
        fs = FileStorage(stream=BytesIO(b"fake"), filename="thumb.png", content_type="image/png")
        url, pid, err = upload_image(fs)
        assert url is None
        assert pid is None
        assert err is not None
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v


def test_upload_video_returns_error_when_no_file():
    """파일 없이 upload_video 호출 → 에러 반환."""
    prev_env = {
        "CLOUDINARY_CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
        "CLOUDINARY_API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
        "CLOUDINARY_API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
    }
    os.environ["CLOUDINARY_CLOUD_NAME"] = "test"
    os.environ["CLOUDINARY_API_KEY"] = "key"
    os.environ["CLOUDINARY_API_SECRET"] = "secret"
    try:
        url, pid, err = upload_video(None)
        assert url is None and pid is None and err is not None
        url2, pid2, err2 = upload_video(FileStorage(stream=BytesIO(b""), filename="", content_type=""))
        assert url2 is None and pid2 is None and err2 is not None
    finally:
        for k, v in prev_env.items():
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]


# ----- Cloudinary 헬퍼: mock 업로드 성공 -----
@patch("cloudinary.uploader.upload")
def test_upload_video_returns_secure_url_when_mocked(mock_upload):
    """Cloudinary 업로드 모킹 시 secure_url, public_id 반환."""
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/test/video/upload/v1/wetube/videos/abc123.mp4",
        "public_id": "wetube/videos/abc123",
    }
    prev = {
        "CLOUDINARY_CLOUD_NAME": os.environ.pop("CLOUDINARY_CLOUD_NAME", None),
        "CLOUDINARY_API_KEY": os.environ.pop("CLOUDINARY_API_KEY", None),
        "CLOUDINARY_API_SECRET": os.environ.pop("CLOUDINARY_API_SECRET", None),
    }
    os.environ["CLOUDINARY_CLOUD_NAME"] = "test"
    os.environ["CLOUDINARY_API_KEY"] = "key"
    os.environ["CLOUDINARY_API_SECRET"] = "secret"
    try:
        fs = FileStorage(stream=BytesIO(b"fake video"), filename="test.mp4", content_type="video/mp4")
        url, pid, err = upload_video(fs)
        assert url == "https://res.cloudinary.com/test/video/upload/v1/wetube/videos/abc123.mp4"
        assert pid == "wetube/videos/abc123"
        assert err is None
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]


@patch("cloudinary.uploader.upload")
def test_upload_image_returns_secure_url_when_mocked(mock_upload):
    """Cloudinary 이미지 업로드 모킹 시 secure_url 반환."""
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/test/image/upload/v1/wetube/thumbnails/thumb.jpg",
        "public_id": "wetube/thumbnails/thumb",
    }
    prev = {
        "CLOUDINARY_CLOUD_NAME": os.environ.pop("CLOUDINARY_CLOUD_NAME", None),
        "CLOUDINARY_API_KEY": os.environ.pop("CLOUDINARY_API_KEY", None),
        "CLOUDINARY_API_SECRET": os.environ.pop("CLOUDINARY_API_SECRET", None),
    }
    os.environ["CLOUDINARY_CLOUD_NAME"] = "test"
    os.environ["CLOUDINARY_API_KEY"] = "key"
    os.environ["CLOUDINARY_API_SECRET"] = "secret"
    try:
        fs = FileStorage(stream=BytesIO(b"fake image"), filename="thumb.jpg", content_type="image/jpeg")
        url, pid, err = upload_image(fs)
        assert url == "https://res.cloudinary.com/test/image/upload/v1/wetube/thumbnails/thumb.jpg"
        assert pid == "wetube/thumbnails/thumb"
        assert err is None
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]


# ----- delete_cloudinary_resource -----
def test_delete_cloudinary_resource_returns_false_when_not_configured():
    """Cloudinary 미설정 시 delete_cloudinary_resource → False."""
    prev = {}
    for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
        prev[key] = os.environ.pop(key, None)
    try:
        assert delete_cloudinary_resource("some_id", "video") is False
        assert delete_cloudinary_resource(None, "video") is False
        assert delete_cloudinary_resource("", "image") is False
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v


# ----- Video 모델 get_video_url, get_thumbnail_url -----
@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저."""
    return db.session.get(User, 1)


@pytest.fixture
def video_local(app_ctx, user):
    """로컬 경로 저장 비디오 (video_url, thumbnail_url 없음)."""
    v = Video(
        title="로컬 비디오",
        video_path="local_video.mp4",
        thumbnail_path="local_thumb.png",
        user_id=user.id,
    )
    db.session.add(v)
    db.session.commit()
    return v


@pytest.fixture
def video_cloudinary(app_ctx, user):
    """Cloudinary URL 저장 비디오."""
    v = Video(
        title="클라우드 비디오",
        video_path="wetube/videos/abc",
        thumbnail_path=None,
        video_url="https://res.cloudinary.com/xxx/video/upload/v1/abc.mp4",
        thumbnail_url="https://res.cloudinary.com/xxx/image/upload/v1/thumb.jpg",
        video_public_id="wetube/videos/abc",
        thumbnail_public_id="wetube/thumbnails/thumb",
        user_id=user.id,
    )
    db.session.add(v)
    db.session.commit()
    return v


def test_get_video_url_returns_cloudinary_url_when_set(app, app_ctx, video_cloudinary):
    """video_url이 있으면 get_video_url() → Cloudinary URL 반환."""
    with app.test_request_context():
        url = video_cloudinary.get_video_url()
    assert url == "https://res.cloudinary.com/xxx/video/upload/v1/abc.mp4"


def test_get_video_url_returns_local_media_path_when_no_url(app, app_ctx, video_local):
    """video_url 없으면 get_video_url() → 로컬 media 경로 반환."""
    with app.test_request_context():
        url = video_local.get_video_url()
    assert "/media/videos/" in url
    assert "local_video.mp4" in url


def test_get_thumbnail_url_returns_cloudinary_url_when_set(app, app_ctx, video_cloudinary):
    """thumbnail_url이 있으면 get_thumbnail_url() → Cloudinary URL 반환."""
    with app.test_request_context():
        url = video_cloudinary.get_thumbnail_url()
    assert url == "https://res.cloudinary.com/xxx/image/upload/v1/thumb.jpg"


def test_get_thumbnail_url_returns_local_path_when_no_url(app, app_ctx, video_local):
    """thumbnail_url 없고 thumbnail_path 있으면 → 로컬 media 경로."""
    with app.test_request_context():
        url = video_local.get_thumbnail_url()
    assert url is not None
    assert "/media/thumbnails/" in url
    assert "local_thumb.png" in url


def test_get_thumbnail_url_returns_none_when_no_thumbnail(app_ctx, user):
    """thumbnail_path, thumbnail_url 모두 없으면 → None."""
    v = Video(title="NoThumb", video_path="x.mp4", user_id=user.id, thumbnail_path=None)
    db.session.add(v)
    db.session.commit()
    with app_ctx.test_request_context():
        assert v.get_thumbnail_url() is None


# ----- Studio 업로드: 로컬 모드 (Cloudinary 미설정) -----
def test_studio_upload_local_saves_video_and_thumbnail(logged_in_client, app_ctx):
    """Cloudinary 미설정 시 POST /studio/upload → 로컬 저장, video_url/thumbnail_url 없음."""
    prev = {}
    for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
        prev[key] = os.environ.pop(key, None)
    try:
        # 최소 mp4 시그니처 (fake file)
        video_data = b"\x00\x00\x00\x20ftypmp42"
        thumb_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        data = {
            "title": "업로드 테스트",
            "description": "설명",
            "video": (BytesIO(video_data), "test.mp4"),
            "thumbnail": (BytesIO(thumb_data), "thumb.png"),
        }
        resp = logged_in_client.post(
            "/studio/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        # DB에서 마지막 Video 확인
        v = Video.query.order_by(Video.id.desc()).first()
        assert v is not None
        assert v.title == "업로드 테스트"
        assert v.video_path
        assert v.thumbnail_path
        # 로컬 모드이므로 video_url, thumbnail_url은 None (또는 미설정)
        # get_video_url은 video_path 기반 경로 반환
        with logged_in_client.application.test_request_context():
            url = v.get_video_url()
        assert "/media/videos/" in url or v.video_path in url
    finally:
        for k, v in prev.items():
            if v is not None:
                os.environ[k] = v


# ----- uploads 폴더 샘플 파일 기반 Cloudinary 업로드 테스트 -----
def _set_cloudinary_env():
    """Cloudinary env 설정 (테스트용)."""
    prev = {
        "CLOUDINARY_CLOUD_NAME": os.environ.pop("CLOUDINARY_CLOUD_NAME", None),
        "CLOUDINARY_API_KEY": os.environ.pop("CLOUDINARY_API_KEY", None),
        "CLOUDINARY_API_SECRET": os.environ.pop("CLOUDINARY_API_SECRET", None),
    }
    os.environ["CLOUDINARY_CLOUD_NAME"] = "test"
    os.environ["CLOUDINARY_API_KEY"] = "key"
    os.environ["CLOUDINARY_API_SECRET"] = "secret"
    return prev


def _restore_cloudinary_env(prev):
    """Cloudinary env 복원."""
    for k, v in prev.items():
        if v is not None:
            os.environ[k] = v
        elif k in os.environ:
            del os.environ[k]


@patch("cloudinary.uploader.upload")
def test_upload_video_with_sample_from_uploads(mock_upload):
    """uploads/videos/sample.mp4 를 이용한 비디오 Cloudinary 업로드 정상 동작."""
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/test/video/upload/v1/wetube/videos/sample.mp4",
        "public_id": "wetube/videos/sample",
    }
    prev = _set_cloudinary_env()
    try:
        if not UPLOADS_SAMPLE_VIDEO.exists():
            pytest.skip("uploads/videos/sample.mp4 샘플 파일이 없습니다.")
        with open(UPLOADS_SAMPLE_VIDEO, "rb") as f:
            fs = FileStorage(stream=f, filename="sample.mp4", content_type="video/mp4")
            url, pid, err = upload_video(fs)
        assert url == "https://res.cloudinary.com/test/video/upload/v1/wetube/videos/sample.mp4"
        assert pid == "wetube/videos/sample"
        assert err is None
        assert mock_upload.called
    finally:
        _restore_cloudinary_env(prev)


@patch("cloudinary.uploader.upload")
def test_upload_thumbnail_with_sample_from_uploads(mock_upload):
    """uploads/thumbnails/sample.png 를 이용한 썸네일 Cloudinary 업로드 정상 동작."""
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/test/image/upload/v1/wetube/thumbnails/sample.png",
        "public_id": "wetube/thumbnails/sample",
    }
    prev = _set_cloudinary_env()
    try:
        if not UPLOADS_SAMPLE_THUMB.exists():
            pytest.skip("uploads/thumbnails/sample.png 샘플 파일이 없습니다.")
        with open(UPLOADS_SAMPLE_THUMB, "rb") as f:
            fs = FileStorage(stream=f, filename="sample.png", content_type="image/png")
            url, pid, err = upload_image(fs, folder="wetube/thumbnails")
        assert "res.cloudinary.com" in url
        assert "wetube/thumbnails" in (pid or "")
        assert err is None
        assert mock_upload.called
    finally:
        _restore_cloudinary_env(prev)


@patch("cloudinary.uploader.upload")
def test_upload_profile_image_with_sample_from_uploads(mock_upload):
    """uploads/profiles/sample.jpg 를 이용한 프로필 이미지 Cloudinary 업로드 정상 동작."""
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/test/image/upload/v1/wetube/profiles/sample.jpg",
        "public_id": "wetube/profiles/sample",
    }
    prev = _set_cloudinary_env()
    try:
        if not UPLOADS_SAMPLE_PROFILE.exists():
            pytest.skip("uploads/profiles/sample.jpg 샘플 파일이 없습니다.")
        with open(UPLOADS_SAMPLE_PROFILE, "rb") as f:
            fs = FileStorage(stream=f, filename="sample.jpg", content_type="image/jpeg")
            url, pid, err = upload_image(fs, folder="wetube/profiles")
        assert "res.cloudinary.com" in url
        assert "wetube/profiles" in (pid or "")
        assert err is None
        assert mock_upload.called
    finally:
        _restore_cloudinary_env(prev)


# ----- User get_profile_image_url (Cloudinary URL 지원) -----
def test_user_get_profile_image_url_returns_cloudinary_url_when_set(app, app_ctx, user):
    """profile_image가 Cloudinary 전체 URL이면 그대로 반환."""
    user.profile_image = "https://res.cloudinary.com/xxx/image/upload/v1/wetube/profiles/abc.jpg"
    user.profile_image_public_id = "wetube/profiles/abc"
    db.session.commit()
    with app.test_request_context():
        url = user.get_profile_image_url()
    assert url == "https://res.cloudinary.com/xxx/image/upload/v1/wetube/profiles/abc.jpg"


def test_user_get_profile_image_url_returns_media_path_when_local(app, app_ctx, user):
    """profile_image가 로컬 파일명이면 media_profile 경로 반환."""
    user.profile_image = "20240101_profile.jpg"
    user.profile_image_public_id = None
    db.session.commit()
    with app.test_request_context():
        url = user.get_profile_image_url()
    assert "/media/profiles/" in url
    assert "20240101_profile.jpg" in url


# ----- Studio 업로드: Cloudinary 모드 + uploads 샘플 -----
@patch("cloudinary.uploader.upload")
def test_studio_upload_cloudinary_with_sample_files(mock_upload, logged_in_client, app_ctx):
    """Cloudinary 설정 시 uploads 샘플로 비디오·썸네일 업로드 → Cloudinary URL 저장."""
    mock_upload.side_effect = [
        {"secure_url": "https://res.cloudinary.com/x/video/upload/v1/sample.mp4", "public_id": "wetube/videos/sample"},
        {"secure_url": "https://res.cloudinary.com/x/image/upload/v1/sample.png", "public_id": "wetube/thumbnails/sample"},
    ]
    prev = _set_cloudinary_env()
    try:
        if not UPLOADS_SAMPLE_VIDEO.exists() or not UPLOADS_SAMPLE_THUMB.exists():
            pytest.skip("uploads 샘플 파일이 없습니다.")
        with open(UPLOADS_SAMPLE_VIDEO, "rb") as vf, open(UPLOADS_SAMPLE_THUMB, "rb") as tf:
            data = {
                "title": "Cloudinary 업로드 테스트",
                "description": "설명",
                "video": (vf, "sample.mp4"),
                "thumbnail": (tf, "sample.png"),
            }
            resp = logged_in_client.post("/studio/upload", data=data, content_type="multipart/form-data", follow_redirects=False)
        assert resp.status_code == 302
        v = Video.query.order_by(Video.id.desc()).first()
        assert v is not None
        assert v.title == "Cloudinary 업로드 테스트"
        assert v.video_url and "res.cloudinary.com" in v.video_url
        assert v.thumbnail_url and "res.cloudinary.com" in v.thumbnail_url
        assert v.video_public_id and v.thumbnail_public_id
    finally:
        _restore_cloudinary_env(prev)


# ----- Auth 프로필 이미지 업로드: Cloudinary 모드 -----
@patch("cloudinary.uploader.upload")
def test_auth_profile_upload_cloudinary_with_sample(mock_upload, logged_in_client, app_ctx):
    """Cloudinary 설정 시 uploads/profiles/sample.jpg 로 프로필 이미지 업로드 → secure_url 저장."""
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/x/image/upload/v1/wetube/profiles/sample.jpg",
        "public_id": "wetube/profiles/sample",
    }
    prev = _set_cloudinary_env()
    try:
        if not UPLOADS_SAMPLE_PROFILE.exists():
            pytest.skip("uploads/profiles/sample.jpg 샘플 파일이 없습니다.")
        with open(UPLOADS_SAMPLE_PROFILE, "rb") as pf:
            data = {
                "nickname": "테스트닉",
                "email": "default@example.com",
                "profile_image": (pf, "sample.jpg"),
            }
            resp = logged_in_client.post(
                "/auth/profile",
                data=data,
                content_type="multipart/form-data",
                follow_redirects=False,
            )
        assert resp.status_code in (200, 302)
        # DB에서 유저 확인
        user = db.session.get(User, 1)
        assert user is not None
        assert user.profile_image and user.profile_image.startswith("https://")
        assert "res.cloudinary.com" in user.profile_image
        assert user.profile_image_public_id and "wetube/profiles" in user.profile_image_public_id
    finally:
        _restore_cloudinary_env(prev)
