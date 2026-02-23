# 02. 설정 (Config)

## 위치

`app/__init__.py` 내 `create_app()`에서 `app.config.from_mapping(...)`으로 설정.

## 업로드 관련 설정

| 키                             | 설명                                     | 기본값 예시                             |
| ------------------------------ | ---------------------------------------- | --------------------------------------- |
| `VIDEO_FOLDER`                 | 비디오 파일 저장 디렉터리 (절대 경로)    | `{프로젝트루트}/uploads/videos`         |
| `THUMBNAIL_FOLDER`             | 썸네일 이미지 저장 디렉터리              | `{프로젝트루트}/uploads/thumbnails`     |
| `MAX_VIDEO_SIZE`               | 비디오 최대 크기 (바이트)                | `2 * 1024**3` (2GB)                     |
| `MAX_THUMBNAIL_SIZE`           | 썸네일 최대 크기 (바이트)                | `5 * 1024**2` (5MB)                     |
| `ALLOWED_VIDEO_EXTENSIONS`     | 허용 비디오 확장자 (set, 소문자)         | `{"mp4", "webm", "mov"}`                |
| `ALLOWED_THUMBNAIL_EXTENSIONS` | 허용 썸네일 확장자                       | `{"jpg", "jpeg", "png", "gif", "webp"}` |
| `DEFAULT_USER_ID`              | 로그인 미연동 시 업로드에 사용할 user_id | `1`                                     |

## DB 설정

| 키                               | 설명                                                                         |
| -------------------------------- | ---------------------------------------------------------------------------- |
| `SQLALCHEMY_DATABASE_URI`        | 환경변수 `DATABASE_URL` 없으면 `sqlite:///{프로젝트루트}/instance/wetube.db` |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False`                                                                      |

## 앱 기동 시 자동 처리

- `VIDEO_FOLDER`, `THUMBNAIL_FOLDER`, `instance` 디렉터리 없으면 `os.makedirs(..., exist_ok=True)`로 생성.
- `db.create_all()`로 테이블 생성.
- `User.query.get(1)`이 없으면 `username=default`, `email=default@example.com` 사용자 생성.

## 확장자·용량 변경 방법

`app/__init__.py`의 `app.config.from_mapping(...)` 블록에서 해당 키 값을 수정하면 된다.
