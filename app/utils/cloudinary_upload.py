"""
Cloudinary 업로드 헬퍼.

동영상·썸네일을 Cloudinary에 업로드하고 secure_url, public_id 반환.
.env: CLOUDINARY_* 필수. 배포에서만 USE_CLOUDINARY_PROXY=1 + CLOUDINARY_API_PROXY.
"""

import os
import tempfile
from typing import Optional, Tuple

# cloudinary 패키지가 없으면 import 시 에러


def _is_cloudinary_configured() -> bool:
    """Cloudinary API 설정이 되어 있는지 확인."""
    return bool(
        os.environ.get("CLOUDINARY_CLOUD_NAME")
        and os.environ.get("CLOUDINARY_API_KEY")
        and os.environ.get("CLOUDINARY_API_SECRET")
    )


def _use_cloudinary_proxy() -> bool:
    """배포 환경(PA 등)에서만 프록시 사용. 로컬에서는 False."""
    return os.environ.get("USE_CLOUDINARY_PROXY", "").strip().lower() in ("1", "true", "yes")


def _get_cloudinary_config() -> dict:
    """Cloudinary config 딕셔너리 반환. api_proxy는 USE_CLOUDINARY_PROXY=1 일 때만 사용 (배포용)."""
    config = {
        "cloud_name": os.environ.get("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.environ.get("CLOUDINARY_API_KEY"),
        "api_secret": os.environ.get("CLOUDINARY_API_SECRET"),
        "secure": True,
    }
    if _use_cloudinary_proxy():
        api_proxy = os.environ.get("CLOUDINARY_API_PROXY", "").strip()
        if api_proxy:
            config["api_proxy"] = api_proxy
    return config


def upload_video(file_storage, resource_type: str = "video") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    비디오 파일을 Cloudinary에 업로드.

    반환: (secure_url, public_id, error_message)
    - 성공 시: (secure_url, public_id, None)
    - 실패 시: (None, None, error_message)
    """
    if not _is_cloudinary_configured():
        return None, None, "Cloudinary API 설정이 없습니다. .env 파일을 확인하세요."

    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(**_get_cloudinary_config())
    except ImportError:
        return None, None, "cloudinary 패키지가 설치되지 않았습니다."

    if not file_storage or not file_storage.filename:
        return None, None, "파일이 선택되지 않았습니다."

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else "mp4"

    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            file_storage.save(tmp.name)
            tmp_path = tmp.name
        try:
            result = cloudinary.uploader.upload(
                tmp_path,
                resource_type="video",
                folder="wetube/videos",
                use_filename=True,
                unique_filename=True,
            )
            secure_url = result.get("secure_url")
            public_id = result.get("public_id")
            return secure_url, public_id, None
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    except Exception as e:
        return None, None, str(e)


def upload_image(file_storage, folder: str = "wetube/thumbnails") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    이미지(썸네일) 파일을 Cloudinary에 업로드.

    반환: (secure_url, public_id, error_message)
    """
    if not _is_cloudinary_configured():
        return None, None, "Cloudinary API 설정이 없습니다."

    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(**_get_cloudinary_config())
    except ImportError:
        return None, None, "cloudinary 패키지가 설치되지 않았습니다."

    if not file_storage or not file_storage.filename:
        return None, None, "파일이 선택되지 않았습니다."

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else "jpg"
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            file_storage.save(tmp.name)
            tmp_path = tmp.name
        try:
            result = cloudinary.uploader.upload(
                tmp_path,
                resource_type="image",
                folder=folder,
                use_filename=True,
                unique_filename=True,
            )
            secure_url = result.get("secure_url")
            public_id = result.get("public_id")
            return secure_url, public_id, None
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    except Exception as e:
        return None, None, str(e)


def delete_cloudinary_resource(public_id: str, resource_type: str = "video") -> bool:
    """Cloudinary에서 리소스 삭제. resource_type: 'video' 또는 'image'."""
    if not public_id or not _is_cloudinary_configured():
        return False
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(**_get_cloudinary_config())
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return True
    except Exception:
        return False
