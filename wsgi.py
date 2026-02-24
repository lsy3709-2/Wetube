"""
Python Anywhere / WSGI 서버용 진입점.
flask run 과 동일하게 app 패키지를 로드합니다.
PA Manual config 시 WSGI 파일에 이 내용을 참고해 작성하세요.
"""
import sys
import os

# 프로젝트 루트를 경로에 추가
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# .env 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

os.environ['FLASK_APP'] = 'app'
from app import app as application
