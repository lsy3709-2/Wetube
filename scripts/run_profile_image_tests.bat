@echo off
REM 프로필 이미지 관련 단위테스트 일괄 실행
cd /d "%~dp0.."
python -m pytest tests/test_utils_image.py tests/test_auth_profile.py -v %*
