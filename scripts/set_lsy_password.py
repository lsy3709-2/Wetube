#!/usr/bin/env python
"""
lsy수정 유저 비밀번호를 1234로 변경.
실행: python scripts/set_lsy_password.py
※ 프로젝트 루트(c:\Wetube\ch05)에서 실행하세요.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User


def main():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username="lsy수정").first()
        if not user:
            print("[오류] lsy수정 사용자를 찾을 수 없습니다.")
            sys.exit(1)
        user.set_password("1234")
        db.session.commit()
        assert user.check_password("1234"), "비밀번호 검증 실패"
        print(f"[완료] lsy수정(id={user.id}) 비밀번호를 1234로 변경했습니다.")


if __name__ == "__main__":
    main()
