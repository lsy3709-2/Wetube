#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
실제 DB 반영 테스트 실행 후 sqlite로 테이블 확인.
실행: python tests/run_real_db_tests_and_verify.py
"""
import os
import subprocess
import sys

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "instance",
    "wetube.db",
)


def run_pytest():
    """실제 DB 반영 테스트 실행."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_real_db_reflect.py",
        "tests/test_watch_real_db.py",
        "-v",
    ]
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return result.returncode == 0


def verify_with_sqlite():
    """Python sqlite3로 테이블 내용 출력."""
    import sqlite3

    if not os.path.exists(DB_PATH):
        print(f"\n[오류] DB 파일 없음: {DB_PATH}")
        return

    print("\n" + "=" * 60)
    print("instance/wetube.db 테이블 확인")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # users
    cur.execute("SELECT id, username, email FROM users")
    rows = cur.fetchall()
    print("\n[users]")
    for r in rows:
        print(f"  id={r['id']} username={r['username']} email={r['email']}")

    # videos
    cur.execute("SELECT id, title, user_id, views, likes FROM videos ORDER BY id")
    rows = cur.fetchall()
    print("\n[videos]")
    for r in rows:
        print(f"  id={r['id']} title={r['title']} user_id={r['user_id']} views={r['views']} likes={r['likes']}")

    # subscriptions
    cur.execute("SELECT subscriber_id, subscribed_to_id FROM subscriptions")
    rows = cur.fetchall()
    print("\n[subscriptions]")
    if rows:
        for r in rows:
            print(f"  subscriber_id={r['subscriber_id']} → subscribed_to_id={r['subscribed_to_id']}")
    else:
        print("  (비어 있음)")

    conn.close()
    print("\n" + "=" * 60)
    print("sqlite3 CLI로 확인: sqlite3 instance/wetube.db")
    print("  SELECT * FROM users;")
    print("  SELECT id, title, views, likes FROM videos;")
    print("  SELECT * FROM subscriptions;")
    print("=" * 60)


def main():
    print("1) 실제 DB 반영 단위 테스트 실행 중...")
    if not run_pytest():
        print("\n테스트 실패. DB 확인을 건너뜁니다.")
        sys.exit(1)

    print("\n2) DB 테이블 내용 확인")
    verify_with_sqlite()


if __name__ == "__main__":
    main()
