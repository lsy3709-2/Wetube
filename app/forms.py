"""
Flask-WTF 폼 클래스 – 로그인, 회원가입 등.
"""
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """로그인 폼 – 아이디/이메일, 비밀번호, 로그인 유지."""

    # 아이디 또는 이메일 (사용자가 편한 것 입력)
    login_id = StringField("아이디/이메일", validators=[DataRequired(message="아이디 또는 이메일을 입력해주세요.")])
    password = PasswordField("비밀번호", validators=[DataRequired(message="비밀번호를 입력해주세요.")])
    remember = BooleanField("로그인 유지", default=False)
