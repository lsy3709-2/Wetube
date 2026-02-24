# Python Anywhere 배포 안내 (WeTube)

WeTube 프로젝트를 Python Anywhere(PA)에 배포하는 방법입니다.

**PA 사용자명: lsy37092**

---

## 1. 사전 준비

- [Python Anywhere](https://www.pythonanywhere.com) 가입
- GitHub 저장소: `https://github.com/lsy3709-2/Wetube.git`
- Cloudinary 계정 (동영상·썸네일 업로드용)

---

## 2. 프로젝트 클론

### 2-1. Bash 콘솔 접속

PA 대시보드 → **Consoles** → **$ Bash** → 새 콘솔 열기

### 2-2. 저장소 클론

```bash
cd ~
git clone https://github.com/lsy3709-2/Wetube.git
cd Wetube
```

> 프로젝트 경로: `/home/lsy37092/Wetube`

---

## 3. 가상환경 생성 및 패키지 설치

```bash
cd ~/Wetube

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치 (기존 requirements.txt 사용)
pip install -r requirements.txt
```

---

## 4. 환경 변수 설정 (.env)

### 4-1. .env 파일 생성

프로젝트 루트에 `.env` 파일을 만듭니다.

```bash
cd ~/Wetube
nano .env
```

### 4-2. 아래 내용 입력 (lsy37092 기준)

```env
# Flask 앱 식별
FLASK_APP=app

# 운영용 시크릿 키 (아래 명령으로 새로 생성 권장)
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=여기에_강한_랜덤_키_입력

# DB (PA 경로 - lsy37092 기준)
DATABASE_URL=sqlite:////home/lsy37092/Wetube/instance/wetube.db

# Cloudinary (동영상·썸네일 업로드)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
# 프록시 경유 시 (Connection refused 시): http://proxy.server:3128
# CLOUDINARY_API_PROXY=

# Flask 모드
FLASK_ENV=production
```

**SECRET_KEY 생성 예시:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Cloudinary 값:** [Cloudinary 대시보드](https://console.cloudinary.com)에서 확인 후 입력

`Ctrl+O` → Enter → `Ctrl+X` 로 저장 후 종료

---

## 5. Web 앱 설정

### 5-1. 새 Web 앱 추가

1. PA 대시보드 → **Web** 탭
2. **Add a new web app** 클릭
3. **경로 설정 화면 (Quickstart 선택 시)**  
   - "Quickstart new Flask project"를 선택하면 경로 입력 화면이 표시됩니다.  
   - **Path** 필드 기본값: `/home/lsy37092/mysite/flask_app.py`  
   - 안내 문구: "Enter a path for a Python file you wish to use to hold your Flask app. If this file already exists, its contents will be overwritten with the new app."
4. **WeTube는 기존 프로젝트**이므로 **Manual configuration**을 선택하세요.  
   (Quickstart는 새 flask_app.py를 생성하여 기존 Wetube 구조를 덮어씁니다)
5. **Python 3.10** (또는 최신) 선택

### 5-1-1. 경로 설정 예시 (flask run 사용 시)

로컬에서 `flask run`으로 실행 중이라면 구조는 다음과 같습니다.

| 구분 | 경로 |
|------|------|
| **프로젝트 루트** | `/home/lsy37092/Wetube` |
| **Flask 앱 패키지** | `/home/lsy37092/Wetube/app` |
| **WSGI 진입 파일** | `/home/lsy37092/Wetube/wsgi.py` |

- `flask run` ↔ `FLASK_APP=app` → `app/__init__.py`의 `app` 객체 사용  
- PA에서는 **Manual configuration** 후 WSGI에 프로젝트 경로(`/home/lsy37092/Wetube`)를 넣고 `from app import app as application`으로 로드

### 5-2. 가상환경 경로 지정

1. **Web** → **Virtualenv** 섹션
2. **Enter path to a virtualenv, if desired** 입력:
   ```
   /home/lsy37092/Wetube/venv
   ```

### 5-3. WSGI 설정

1. **Web** → **Code** 섹션의 **WSGI configuration file** 링크 클릭
2. 기존 내용을 삭제하고 아래로 교체:

```python
import sys
import os

# 프로젝트 경로 추가
path = '/home/lsy37092/Wetube'
if path not in sys.path:
    sys.path.insert(0, path)

# .env 로드 (load_dotenv)
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

# Flask 앱
os.environ['FLASK_APP'] = 'app'
from app import app as application
```

3. **Save** 클릭

### 5-4. Static files 매핑 (선택)

정적 파일(CSS, JS)을 직접 서빙하려면:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/lsy37092/Wetube/app/static/` |

**Web** → **Static files** 에서 추가

---

## 6. DB 초기화

앱 최초 실행 시 `db.create_all()`로 테이블이 자동 생성됩니다. 수동 실행이 필요하면:

```bash
cd ~/Wetube
source venv/bin/activate
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('DB 테이블 생성 완료')
"
```

---

## 7. 앱 재시작

**Web** 탭 → **Reload lsy37092.pythonanywhere.com** 클릭

---

## 8. 접속 확인

브라우저에서 다음 주소로 접속:

- **무료 계정:** `https://lsy37092.pythonanywhere.com`
- **유료 계정:** 설정한 커스텀 도메인

---

## 9. 환경 변수 (Web 탭) – .env 대신 사용 시

`.env` 대신 PA Web 화면에서 직접 입력하려면:

1. **Web** → **Your web app** → **Code**
2. **Environment variables** 섹션에 추가:

| Name | Value |
|------|-------|
| `FLASK_APP` | `app` |
| `SECRET_KEY` | `생성한_64자_hex_문자열` |
| `DATABASE_URL` | `sqlite:////home/lsy37092/Wetube/instance/wetube.db` |
| `CLOUDINARY_CLOUD_NAME` | `your_cloud_name` |
| `CLOUDINARY_API_KEY` | `your_api_key` |
| `CLOUDINARY_API_SECRET` | `your_api_secret` |
| `FLASK_ENV` | `production` |

---

## 10. 업데이트 (재배포)

코드 변경 후:

```bash
cd ~/Wetube
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

이후 **Web** 탭에서 **Reload** 클릭

---

## 11. 문제 해결

| 증상 | 확인 사항 |
|------|-----------|
| 500 Internal Server Error | **Web** → **Error log** 확인, 가상환경 경로·WSGI 경로 확인 |
| DB 관련 오류 | `DATABASE_URL` 경로, `instance/` 폴더 생성 여부 확인 |
| 정적 파일 404 | Static files 매핑 추가 |
| Cloudinary 오류 | `.env` 또는 환경 변수에 API 키/시크릿 정확히 입력 |
| Connection refused (api.cloudinary.com) | PA 무료는 아웃바운드 제한 있음. 유료 업그레이드 또는 프록시 사용 시 `.env`에 `CLOUDINARY_API_PROXY=http://proxy.server:3128` 추가 |
| CSRF 오류 | `SECRET_KEY`가 설정되었는지 확인 |

---

## 12. 경로 요약 (lsy37092)

| 항목 | 경로 |
|------|------|
| 프로젝트 | `/home/lsy37092/Wetube` |
| 가상환경 | `/home/lsy37092/Wetube/venv` |
| SQLite DB | `/home/lsy37092/Wetube/instance/wetube.db` |
| .env | `/home/lsy37092/Wetube/.env` |
