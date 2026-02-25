"""
Flask 앱 팩토리 – 업로드·DB 포함.

기능: create_app()으로 앱 인스턴스를 생성하고,
      설정(config), DB, 업로드 폴더, Blueprint 등록, 테이블·기본 유저 생성을 수행합니다.
"""

import os

# .env 파일 로드 (Cloudinary API 키 등)
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone

from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# ---------------------------------------------------------------------------
# DB 확장 객체 (모듈 레벨)
# 기능: Flask-SQLAlchemy 확장. create_app() 내에서 init_app(app)으로 앱에 연결합니다.
#       라우트·모델에서 from app import db 로 사용합니다.
# ---------------------------------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    """
    앱 팩토리 함수.
    기능: Flask 앱 생성 → 설정 → 폴더 생성 → DB·Blueprint 등록 → 테이블·기본 유저 생성 후 앱 반환.
    """
    # ----- 1) Flask 앱 인스턴스 생성 -----
    app = Flask(__name__)

    # ----- 2) 프로젝트 루트·업로드 경로 계산 -----
    # 기능: __file__ 기준으로 app 폴더의 상위(ch05)를 project_root로 두고,
    #       비디오·썸네일 저장 경로를 만듭니다.
    project_root = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    video_folder = os.path.join(project_root, "uploads", "videos")
    thumbnail_folder = os.path.join(project_root, "uploads", "thumbnails")
    profile_folder = os.path.join(project_root, "uploads", "profiles")

    # ----- 3) 설정(config) 등록 -----
    # 기능: DB URI, 업로드 폴더·용량·확장자, 기본 user_id 등을 앱 설정에 넣습니다.
    #       라우트에서 current_app.config["VIDEO_FOLDER"] 등으로 읽습니다.
    default_db_path = os.path.join(project_root, "instance", "wetube.db")
    # Windows에서 백슬래시가 URI로 잘못 해석되지 않도록 슬래시로 통일
    default_db_uri = "sqlite:///" + os.path.normpath(default_db_path).replace("\\", "/")
    # DATABASE_URL이 PA 등 다른 환경 경로일 때, 로컬에서는 해당 경로가 없으면 기본 경로 사용
    db_uri = os.environ.get("DATABASE_URL", default_db_uri)
    if db_uri.startswith("sqlite:///"):
        db_file_path = db_uri.replace("sqlite:///", "").replace("/", os.sep)
        db_dir = os.path.dirname(db_file_path)
        if not os.path.exists(db_dir):
            db_uri = default_db_uri
    app.config.from_mapping(
        # 세션·flash·CSRF 등 서명용. .env의 SECRET_KEY 사용, 없으면 개발용 고정값.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-frontend-only"),
        # DB: 환경변수 DATABASE_URL 사용, 단 로컬에서 해당 경로가 없으면 프로젝트 instance/wetube.db
        SQLALCHEMY_DATABASE_URI=db_uri,
        # 모델 속성 변경 추적 비활성화. True면 변경 시 before_commit 등 이벤트 발생·오버헤드 있음. 불필요하면 False 권장.
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # 업로드 폴더 (절대 경로)
        VIDEO_FOLDER=video_folder,
        THUMBNAIL_FOLDER=thumbnail_folder,
        PROFILE_IMAGE_FOLDER=profile_folder,
        # 업로드 제한 (바이트)
        MAX_VIDEO_SIZE=2 * 1024 * 1024 * 1024,  # 2GB
        MAX_THUMBNAIL_SIZE=5 * 1024 * 1024,  # 5MB
        MAX_PROFILE_IMAGE_SIZE=5 * 1024 * 1024,  # 5MB
        # 허용 확장자 (set, 소문자로 비교)
        ALLOWED_VIDEO_EXTENSIONS={"mp4", "webm", "mov"},
        ALLOWED_THUMBNAIL_EXTENSIONS={"jpg", "jpeg", "png", "gif", "webp"},
        ALLOWED_PROFILE_IMAGE_EXTENSIONS={"jpg", "jpeg", "png", "gif", "webp"},
        ALLOWED_IMAGE_EXTENSIONS={"jpg", "jpeg", "png", "gif", "webp"},  # validate_image_file 호환
        # 로그인 미연동 시 업로드에 사용할 user_id (기본 1)
        DEFAULT_USER_ID=1,
    )

    # ----- 4) 업로드·DB용 디렉터리 생성 -----
    # 기능: 폴더가 없으면 생성. exist_ok=True 로 이미 있어도 에러 없음.
    os.makedirs(app.config["VIDEO_FOLDER"], exist_ok=True)
    os.makedirs(app.config["THUMBNAIL_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PROFILE_IMAGE_FOLDER"], exist_ok=True)
    instance_path = os.path.join(project_root, "instance")
    os.makedirs(instance_path, exist_ok=True)

    # 개발 시 실제 사용 중인 DB 경로 확인용 (wetube.db 미반영 시 점검)
    _uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if _uri.startswith("sqlite:///"):
        _path = _uri.replace("sqlite:///", "").replace("/", os.sep)
        print(f"[DB] 사용 중: {os.path.abspath(_path)}")

    # ----- 5) DB 확장을 현재 앱에 연결 -----
    # 기능: db.Model, db.session, db.create_all() 등을 이 앱 컨텍스트에서 사용 가능하게 함.
    db.init_app(app)

    # ----- 5-0) CSRF 보호 (댓글 등 수동 폼용) -----
    CSRFProtect(app)

    # ----- 5-1) Flask-Login 초기화 -----
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "로그인이 필요합니다."

    @login_manager.user_loader
    def load_user(user_id):
        """세션에서 사용자 ID로 유저 객체 반환."""
        from app.models import User
        try:
            return db.session.get(User, int(user_id)) if user_id else None
        except (ValueError, TypeError):
            return None

    # ----- 6) Blueprint 등록 -----
    # 기능: URL 접두사별로 라우트를 묶어 등록. / → main, /auth → auth, /studio → studio, /admin → admin.
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.studio import studio_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.comments import comments_bp
    from app.routes.likes import likes_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(likes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(studio_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # 템플릿 필터: 상대 시간 표시 (예: "방금 전", "3일 전")
    @app.template_filter("timesince")
    def timesince_filter(dt):
        if not dt:
            return ""
        try:
            now = datetime.now(timezone.utc)
            if getattr(dt, "tzinfo", None) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = now - dt
            if delta.days > 0:
                return f"{delta.days}일 전"
            if delta.seconds >= 3600:
                return f"{delta.seconds // 3600}시간 전"
            if delta.seconds >= 60:
                return f"{delta.seconds // 60}분 전"
            return "방금 전"
        except (TypeError, ValueError, OverflowError):
            return dt.strftime("%Y. %m. %d.") if hasattr(dt, "strftime") else str(dt)

    # 403: 로그인 미구현 시 수정/삭제는 소유자(DEFAULT_USER_ID)만 허용
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    # ----- 7) 모델 로드 후 테이블·기본 유저 생성 -----
    # 기능: User, Video 모델을 로드한 뒤 create_all()로 테이블 생성.
    #       user_id=1 이 없으면 default 유저를 만들어 업로드 시 DEFAULT_USER_ID 사용 가능하게 함.
    from app import models  # noqa: F401
    from app.models import User

    # 앱 컨텍스트 안에서만 DB 작업 가능 (create_all, session 등)
    with app.app_context():
        # 등록된 모델(User, Video) 기준으로 테이블 생성. 없으면 생성, 있으면 스킵
        db.create_all()
        # 기존 DB에 video_url, thumbnail_url 컬럼 추가 (Cloudinary 지원, 없을 때만)
        try:
            from sqlalchemy import text
            insp = db.inspect(db.engine)
            existing = {c["name"] for c in insp.get_columns("videos")} if "videos" in insp.get_table_names() else set()
            for col in ("video_url", "thumbnail_url"):
                if col not in existing:
                    db.session.execute(text(f"ALTER TABLE videos ADD COLUMN {col} VARCHAR(512)"))
                    db.session.commit()
        except Exception:
            db.session.rollback()
        # users 테이블에 is_admin 컬럼 없으면 추가 (기존 DB 마이그레이션)
        try:
            from sqlalchemy import text
            insp = db.inspect(db.engine)
            if "users" in insp.get_table_names():
                user_cols = {c["name"] for c in insp.get_columns("users")}
                if "is_admin" not in user_cols:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                    db.session.commit()
        except Exception:
            db.session.rollback()
        # user_id=1 이 없으면 업로드 시 DEFAULT_USER_ID(1)를 쓸 수 없으므로 기본 유저 생성
        if db.session.get(User, 1) is None:
            default_user = User(
                username="default",
                email="default@example.com",
            )
            default_user.set_password("default")
            db.session.add(default_user)
            db.session.commit()
        # 기본 관리자 계정 admin / admin1234 (없을 때만 생성)
        admin_user = User.query.filter_by(username="admin").first()
        if admin_user is None:
            admin_user = User(username="admin", email="admin@example.com", is_admin=True)
            admin_user.set_password("admin1234")
            db.session.add(admin_user)
            db.session.commit()

    return app


# ---------------------------------------------------------------------------
# 모듈 레벨 앱 인스턴스
# flask run 시: FLASK_APP=app 이면 Flask CLI가 이 모듈(app/__init__.py)만 import.
#               위 create_app() 실행 후 여기서 만든 app 을 가져다 WSGI 서버를 띄움. __main__.py 는 실행 안 함.
# ---------------------------------------------------------------------------
app = create_app()

# ---------------------------------------------------------------------------
# 직접 실행 시 진입점 (python -m app 또는 python app/__init__.py)
# 차이점:
#   - flask run: 이 블록은 실행되지 않음. Flask CLI가 app 객체만 로드하고 자체 서버로 기동.
#   - python -m app: 패키지 app 로드 → __init__.py 실행(app 생성) → __main__.py 실행(app.run 호출).
#   - python app/__init__.py: 이 파일을 스크립트로 실행 → __init__.py 전체 실행 → 아래 app.run() 실행.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    # sqlite:///C:/path/to/wetube.db → 실제 파일 경로만 표시
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "").replace("/", os.sep)
        print(f"[DB] 사용 중: {db_path}")
    print("등록된 라우트: / /auth/login /auth/register /auth/profile /studio ...")
    print("중요: 5000 포트를 쓰는 다른 프로그램(기존 Flask 등)이 있으면 먼저 종료하세요.")
    print("      그렇지 않으면 /studio/ 에서 404가 납니다.")
    app.run(debug=True, host="127.0.0.1", port=5000)  # use_reloader 기본 True → 코드 변경 시 자동 재시작
