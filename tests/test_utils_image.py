# 단위 테스트 – 이미지 검증 유틸 (validate_image_file)

from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from app.utils.image import validate_image_file


@pytest.fixture
def valid_png_file():
    """유효한 PNG 이미지 FileStorage."""
    buf = BytesIO()
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="red")
    img.save(buf, format="PNG")
    buf.seek(0)
    data = buf.getvalue()
    fs = FileStorage(stream=BytesIO(data), filename="test.png", content_type="image/png")
    return fs


@pytest.fixture
def valid_jpg_file():
    """유효한 JPEG 이미지 FileStorage."""
    buf = BytesIO()
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="green")
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    data = buf.getvalue()
    fs = FileStorage(stream=BytesIO(data), filename="photo.jpg", content_type="image/jpeg")
    return fs


def test_validate_image_file_empty_file():
    """파일 없음 → (False, 에러메시지)."""
    ok, msg = validate_image_file(None, {"jpg", "png"}, 1024)
    assert ok is False
    assert "파일" in msg

    ok, msg = validate_image_file(FileStorage(), {"jpg", "png"}, 1024)
    assert ok is False


def test_validate_image_file_invalid_extension(valid_png_file):
    """허용되지 않는 확장자 → (False, 에러메시지)."""
    ok, msg = validate_image_file(valid_png_file, {"jpg", "gif"}, 1024 * 1024)
    assert ok is False
    assert "허용" in msg or "형식" in msg


def test_validate_image_file_no_extension():
    """확장자 없음 → (False, 에러메시지)."""
    fs = FileStorage(stream=BytesIO(b"x"), filename="noext", content_type="application/octet-stream")
    ok, msg = validate_image_file(fs, {"jpg", "png"}, 1024)
    assert ok is False


def test_validate_image_file_too_large(valid_png_file):
    """파일 크기 초과 → (False, 에러메시지)."""
    ok, msg = validate_image_file(valid_png_file, {"png"}, 10)
    assert ok is False
    assert "크기" in msg or "MB" in msg


def test_validate_image_file_invalid_image():
    """이미지가 아닌 파일(텍스트) → (False, 에러메시지)."""
    fs = FileStorage(
        stream=BytesIO(b"this is not an image file"),
        filename="fake.png",
        content_type="image/png",
    )
    ok, msg = validate_image_file(fs, {"png"}, 1024 * 1024)
    assert ok is False
    assert "유효하지 않은" in msg or "이미지" in msg


def test_validate_image_file_valid_png(valid_png_file):
    """유효한 PNG → (True, None)."""
    ok, msg = validate_image_file(valid_png_file, {"jpg", "jpeg", "png", "gif", "webp"}, 5 * 1024 * 1024)
    assert ok is True
    assert msg is None


def test_validate_image_file_valid_jpg(valid_jpg_file):
    """유효한 JPEG → (True, None)."""
    ok, msg = validate_image_file(valid_jpg_file, {"jpg", "jpeg", "png", "gif", "webp"}, 5 * 1024 * 1024)
    assert ok is True
    assert msg is None


def test_validate_image_file_preserves_stream_for_save(valid_png_file):
    """검증 후 file_storage를 다시 읽을 수 있어야 save 가능."""
    ok, _ = validate_image_file(valid_png_file, {"png"}, 5 * 1024 * 1024)
    assert ok is True
    valid_png_file.seek(0)
    data_after = valid_png_file.read()
    assert len(data_after) > 0
