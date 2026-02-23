#!/usr/bin/env python
"""
lsy 유저 DB 업데이트 – username lsy수정, email lsy수정@naver.com, nickname lsy수정, password 1234수정
실행: python scripts/update_lsy_user.py
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
        # 기존 lsy 또는 lsy수정 유저 조회
        user = User.query.filter(User.username.in_(["lsy", "lsy수정"])).first()
        if user:
            user.username = "lsy수정"
            user.email = "lsy수정@naver.com"
            user.nickname = "lsy수정"
            user.set_password("1234수정")
            db.session.commit()
            print(f"[완료] 기존 유저(id={user.id}) 업데이트: lsy수정 / 1234수정 / lsy수정@naver.com")
        else:
            user = User(username="lsy수정", email="lsy수정@naver.com", nickname="lsy수정")
            user.set_password("1234수정")
            db.session.add(user)
            db.session.commit()
            print(f"[완료] 새 유저(id={user.id}) 생성: lsy수정 / 1234수정 / lsy수정@naver.com")

        # 검증
        u = User.query.filter_by(username="lsy수정").first()
        assert u.check_password("1234수정"), "비밀번호 검증 실패"
        assert u.email == "lsy수정@naver.com", "이메일 검증 실패"
        assert u.nickname == "lsy수정", "닉네임 검증 실패"
        print("[검증] check_password('1234수정') = True")


if __name__ == "__main__":
    main()
