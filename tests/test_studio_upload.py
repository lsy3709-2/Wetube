# 단위 테스트 – Studio 업로드 확장자·검증 (화면 미사용)
import io

import pytest

from app.routes.studio import _allowed_file


# ----- _allowed_file 확장자 검증 -----
def test_allowed_file_accepts_mp4():
    """허용 확장자 mp4 → True."""
    assert _allowed_file("video.mp4", {"mp4", "webm", "mov"}) is True


def test_allowed_file_accepts_webm_mov():
    """허용 확장자 webm, mov → True."""
    assert _allowed_file("a.webm", {"mp4", "webm", "mov"}) is True
    assert _allowed_file("b.mov", {"mp4", "webm", "mov"}) is True


def test_allowed_file_rejects_avi_mkv():
    """비허용 확장자 avi, mkv → False."""
    allowed = {"mp4", "webm", "mov"}
    assert _allowed_file("video.avi", allowed) is False
    assert _allowed_file("video.mkv", allowed) is False


def test_allowed_file_none_or_empty_filename():
    """filename None 또는 빈 문자열 → False."""
    allowed = {"mp4", "webm", "mov"}
    assert _allowed_file(None, allowed) is False
    assert _allowed_file("", allowed) is False


def test_allowed_file_no_extension():
    """확장자 없음(점 없음) → False."""
    assert _allowed_file("novideo", {"mp4", "webm", "mov"}) is False


def test_allowed_file_case_insensitive():
    """확장자 대소문자 구분 없음 (소문자로 비교)."""
    allowed = {"mp4", "webm", "mov"}
    assert _allowed_file("v.MP4", allowed) is True
    assert _allowed_file("v.Mp4", allowed) is True
