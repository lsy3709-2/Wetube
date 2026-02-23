"""
이미지 파일 검증 유틸 – 프로필 이미지 업로드용.
"""

from io import BytesIO

from PIL import Image


def validate_image_file(file_storage, allowed_extensions, max_size_bytes):
    """
    프로필 이미지 파일 유효성 검사.

    검사 항목:
    1. 파일 확장자 (allowed_extensions)
    2. 파일 크기 (max_size_bytes)
    3. Pillow Image.verify()로 실제 이미지 파일 여부 확인

    반환: (True, None) 성공 시, (False, 에러메시지) 실패 시
    """
    if not file_storage or not file_storage.filename:
        return False, "파일이 선택되지 않았습니다."

    filename = file_storage.filename
    if "." not in filename:
        return False, f"허용되지 않는 파일 형식입니다. 허용: {', '.join(sorted(allowed_extensions))}"

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        return False, f"허용되지 않는 파일 형식입니다. 허용: {', '.join(sorted(allowed_extensions))}"

    file_storage.seek(0)
    data = file_storage.read()
    file_storage.seek(0)

    if len(data) > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        return False, f"파일 크기가 너무 큽니다. 최대 {max_mb}MB까지 업로드할 수 있습니다."

    # Pillow로 실제 이미지 파일 여부 검증
    try:
        img = Image.open(BytesIO(data))
        img.verify()
    except Exception:
        return False, "유효하지 않은 이미지 파일입니다. 손상되었거나 이미지 형식이 아닐 수 있습니다."

    return True, None
