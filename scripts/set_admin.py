#!/usr/bin/env python
"""
지정한 username을 관리자로 설정. 실행: python scripts/set_admin.py [username]
예: python scripts/set_admin.py lsy수정
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User


def main():
    username = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not username:
        print("사용법: python scripts/set_admin.py [username]")
        print("예: python scripts/set_admin.py lsy수정")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"[오류] 사용자 '{username}'를 찾을 수 없습니다.")
            sys.exit(1)
        user.is_admin = True
        db.session.commit()
        print(f"[완료] {username}(id={user.id})을(를) 관리자로 설정했습니다.")


if __name__ == "__main__":
    main()
