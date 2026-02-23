"""인증 라우트 – 로그인/회원가입/프로필."""

import os
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from app import db
from app.forms import LoginForm
from app.models import User
from app.utils.image import validate_image_file

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _is_cloudinary_enabled():
    """Cloudinary 환경변수 설정 여부."""
    return bool(
        os.environ.get("CLOUDINARY_CLOUD_NAME")
        and os.environ.get("CLOUDINARY_API_KEY")
        and os.environ.get("CLOUDINARY_API_SECRET")
    )


def _save_profile_image(profile_file, user):
    """
    프로필 이미지를 Cloudinary 또는 로컬에 저장.
    Cloudinary 사용 시: profile_image에 secure_url, profile_image_public_id에 public_id 저장.
    로컬 사용 시: profile_image에 파일명 저장.
    """
    save_dir = current_app.config["PROFILE_IMAGE_FOLDER"]

    # 기존 프로필 이미지 삭제 (로컬 파일 또는 Cloudinary)
    if user.profile_image:
        if user.profile_image.startswith(("http://", "https://")):
            # Cloudinary: public_id로 삭제
            if user.profile_image_public_id:
                from app.utils.cloudinary_upload import delete_cloudinary_resource
                delete_cloudinary_resource(user.profile_image_public_id, "image")
        else:
            old_path = os.path.join(save_dir, user.profile_image)
            if os.path.isfile(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
        user.profile_image = None
        user.profile_image_public_id = None

    if _is_cloudinary_enabled():
        from app.utils.cloudinary_upload import upload_image
        secure_url, public_id, err = upload_image(profile_file, folder="wetube/profiles")
        if err:
            flash(err, "error")
            raise ValueError(err)
        user.profile_image = secure_url
        user.profile_image_public_id = public_id
    else:
        base_name = secure_filename(profile_file.filename) or "profile"
        if "." in base_name:
            name_part, ext_part = base_name.rsplit(".", 1)
            ext_part = ext_part.lower() if ext_part else "jpg"
        else:
            name_part, ext_part = base_name, "jpg"
        timestamp_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp_prefix}_{name_part}.{ext_part}".replace(" ", "_")
        if not safe_name or safe_name.startswith("."):
            safe_name = f"{timestamp_prefix}_profile.{ext_part}"
        try:
            profile_file.save(os.path.join(save_dir, safe_name))
        except OSError as e:
            flash(f"프로필 이미지 저장 실패: {e}", "error")
            raise ValueError(str(e))
        user.profile_image = safe_name


def _is_safe_redirect_url(url):
    """open redirect 방지: 상대 경로 또는 같은 호스트만 허용."""
    if not url or not url.strip():
        return False
    # // 로 시작하면 외부 URL
    if url.startswith("//"):
        return False
    # 프로토콜로 시작하면 외부 URL
    if ":" in url[:8] and url.split(":")[0].lower() in ("http", "https", "ftp"):
        return False
    # / 로 시작하는 상대 경로 허용
    return url.startswith("/")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == "GET":
        # 이미 로그인된 사용자는 홈으로
        if current_user.is_authenticated:
            return redirect(url_for("main.index"))
        return render_template("auth/login.html", form=form)

    # POST: 로그인 처리
    if not form.validate_on_submit():
        for _field, errors in form.errors.items():
            for msg in errors:
                flash(msg, "error")
        return render_template("auth/login.html", form=form), 400

    login_id = (form.login_id.data or "").strip()
    password = form.password.data or ""
    remember = bool(form.remember.data)

    if not login_id or not password:
        flash("아이디/이메일과 비밀번호를 입력해주세요.", "error")
        return render_template("auth/login.html", form=form), 400

    # 이메일 또는 사용자명 중 하나라도 일치하는 사용자 조회
    user = User.query.filter(
        or_(User.email == login_id, User.username == login_id)
    ).first()

    if user is None or not user.check_password(password):
        flash("아이디/이메일 또는 비밀번호가 올바르지 않습니다.", "error")
        return render_template("auth/login.html", form=form), 400

    login_user(user, remember=remember)
    flash("로그인되었습니다.", "success")
    next_url = request.args.get("next")
    if next_url and _is_safe_redirect_url(next_url):
        return redirect(next_url)
    return redirect(url_for("main.index"))


@auth_bp.route("/logout", methods=["GET"])
def logout():
    logout_user()
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    # POST: 회원가입 처리
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""
    password_confirm = request.form.get("password_confirm") or ""
    nickname = (request.form.get("nickname") or "").strip() or None

    # 검증 1: 비밀번호 확인 일치
    if password != password_confirm:
        flash("비밀번호와 비밀번호 확인이 일치하지 않습니다.", "error")
        return render_template(
            "auth/register.html",
            username=username,
            email=email,
            nickname=nickname or "",
        ), 400

    # 검증 2: 필수 항목
    if not username or not email or not password:
        flash("사용자명, 이메일, 비밀번호는 필수입니다.", "error")
        return render_template(
            "auth/register.html",
            username=username,
            email=email,
            nickname=nickname or "",
        ), 400

    # 검증 3: 중복 가입 방지
    if User.query.filter_by(username=username).first():
        flash(f"이미 사용 중인 사용자명입니다: {username}", "error")
        return render_template(
            "auth/register.html",
            username=username,
            email=email,
            nickname=nickname or "",
        ), 400
    if User.query.filter_by(email=email).first():
        flash(f"이미 사용 중인 이메일입니다: {email}", "error")
        return render_template(
            "auth/register.html",
            username=username,
            email=email,
            nickname=nickname or "",
        ), 400

    # 저장: 비밀번호 해싱 후 회원가입
    user = User(username=username, email=email, nickname=nickname)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # 회원가입 성공 즉시 자동 로그인
    login_user(user)
    flash("회원가입이 완료되었습니다.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "GET":
        return render_template("auth/profile.html")

    # POST: 회원정보 수정
    nickname = (request.form.get("nickname") or "").strip() or None
    email = (request.form.get("email") or "").strip()
    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    new_password_confirm = request.form.get("new_password_confirm") or ""

    # 1. 이메일 필수
    if not email:
        flash("이메일은 필수입니다.", "error")
        return render_template(
            "auth/profile.html",
            nickname=nickname or current_user.nickname or "",
            email=email or current_user.email,
        ), 400

    # 2. 이메일 중복 검사 (현재 사용자 제외)
    existing = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing:
        flash(f"이미 사용 중인 이메일입니다: {email}", "error")
        return render_template(
            "auth/profile.html",
            nickname=nickname or current_user.nickname or "",
            email=email,
        ), 400

    # 3. 비밀번호 변경 로직
    if new_password:
        if not current_user.check_password(current_password):
            flash("현재 비밀번호가 올바르지 않습니다.", "error")
            return render_template(
                "auth/profile.html",
                nickname=nickname or current_user.nickname or "",
                email=email,
            ), 400
        if new_password != new_password_confirm:
            flash("새 비밀번호와 확인이 일치하지 않습니다.", "error")
            return render_template(
                "auth/profile.html",
                nickname=nickname or current_user.nickname or "",
                email=email,
            ), 400
        if len(new_password) < 4:
            flash("새 비밀번호는 4자 이상이어야 합니다.", "error")
            return render_template(
                "auth/profile.html",
                nickname=nickname or current_user.nickname or "",
                email=email,
            ), 400
        current_user.set_password(new_password)

    # 4. 프로필 이미지 업로드 (선택)
    profile_file = request.files.get("profile_image")
    if profile_file and profile_file.filename:
        allowed_ext = current_app.config.get(
            "ALLOWED_IMAGE_EXTENSIONS",
            current_app.config.get("ALLOWED_PROFILE_IMAGE_EXTENSIONS", {"jpg", "jpeg", "png", "gif", "webp"}),
        )
        max_size = current_app.config.get("MAX_PROFILE_IMAGE_SIZE", 5 * 1024 * 1024)
        ok, err_msg = validate_image_file(profile_file, allowed_ext, max_size)
        if not ok:
            flash(err_msg, "error")
            return render_template(
                "auth/profile.html",
                nickname=nickname or current_user.nickname or "",
                email=email or current_user.email,
            ), 400

        try:
            _save_profile_image(profile_file, current_user)
        except ValueError:
            return render_template(
                "auth/profile.html",
                nickname=nickname or current_user.nickname or "",
                email=email or current_user.email,
            ), 400

    # 5. 변경 사항 저장
    current_user.nickname = nickname
    current_user.email = email
    db.session.commit()
    flash("회원정보가 수정되었습니다.", "success")
    return redirect(url_for("auth.profile"))
