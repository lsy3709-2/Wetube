#!/usr/bin/env python
"""
프로필 이미지 관련 단위테스트 일괄 실행.
- validate_image_file() (app/utils/image.py)
- 프로필 이미지 업로드 (auth/profile POST)

실행: python scripts/run_profile_image_tests.py
"""
import subprocess
import sys
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).resolve().parent.parent
TESTS = [
    "tests/test_utils_image.py",
    "tests/test_auth_profile.py",
]

if __name__ == "__main__":
    cmd = [sys.executable, "-m", "pytest"] + TESTS + ["-v"] + sys.argv[1:]
    result = subprocess.run(cmd, cwd=ROOT)
    sys.exit(result.returncode)
