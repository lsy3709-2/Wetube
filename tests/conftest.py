# pytest 픽스처 – Flask 앱·클라이언트·DB
import os
from pathlib import Path

import pytest

from app import create_app, db

# 테스트 후 DB 검증용: USE_TEST_DB_FILE=1 이면 파일 DB 사용 (instance/test_pytest.db)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DB_FILE = PROJECT_ROOT / "instance" / "test_pytest.db"
TEST_DB_URI = "sqlite:///" + str(TEST_DB_FILE).replace("\\", "/")


@pytest.fixture
def app():
    """
    테스트용 Flask 앱. 기본은 in-memory SQLite.
    USE_TEST_DB_FILE=1 이면 instance/test_pytest.db 사용 → 테스트 후 sqlite3/DB Browser로 검증 가능.
    """
    prev = os.environ.get("DATABASE_URL")
    use_file = os.environ.get("USE_TEST_DB_FILE", "").strip() == "1"
    if use_file:
        TEST_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        if TEST_DB_FILE.exists():
            TEST_DB_FILE.unlink()
        os.environ["DATABASE_URL"] = TEST_DB_URI
        print(f"\n[conftest] 파일 DB 사용: {TEST_DB_FILE}")
    else:
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    try:
        app = create_app()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False  # 테스트 시 CSRF 검증 비활성화
        yield app
    finally:
        if prev is not None:
            os.environ["DATABASE_URL"] = prev
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client, app_ctx):
    """로그인된 test client (default/default). Studio 등 login_required 라우트 테스트용."""
    client.post(
        "/auth/login",
        data={"login_id": "default", "password": "default"},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def app_ctx(app):
    """앱 컨텍스트 (모델/DB 테스트용)."""
    with app.app_context():
        yield app


@pytest.fixture
def real_app():
    """실제 DB 사용 (instance/wetube.db) – 시드 데이터 삽입용."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def real_client(real_app):
    """실제 DB용 Flask test client."""
    return real_app.test_client()


@pytest.fixture
def real_app_ctx(real_app):
    """실제 DB 앱 컨텍스트."""
    with real_app.app_context():
        yield real_app
