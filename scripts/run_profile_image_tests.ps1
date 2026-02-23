# 프로필 이미지 관련 단위테스트 일괄 실행
Set-Location $PSScriptRoot\..
python -m pytest tests/test_utils_image.py tests/test_auth_profile.py -v @args
