# 03. 모델 (Models)

## 구조

- `app/models/__init__.py`: `User`, `Video` export
- `app/models/user.py`: User 모델 (Video FK용)
- `app/models/video.py`: Video 모델

## User (`app/models/user.py`)

| 컬럼                    | 타입                   | 비고 |
| ----------------------- | ---------------------- | ---- |
| id                      | Integer, PK            |      |
| username                | String(80), unique     |      |
| email                   | String(120), unique    |      |
| password_hash           | String(255)            |      |
| nickname                | String(80), nullable   |      |
| profile_image           | String(255), nullable  |      |
| profile_image_public_id | String(255), nullable  |      |
| is_admin                | Boolean, default False |      |
| created_at              | DateTime               |      |
| updated_at              | DateTime               |      |

- **역할**: Video의 `user_id` FK 대상. 업로드 시 `DEFAULT_USER_ID`(1) 사용.

## Video (`app/models/video.py`)

| 컬럼                | 타입                           | 비고                            |
| ------------------- | ------------------------------ | ------------------------------- |
| id                  | Integer, PK                    |                                 |
| title               | String(200)                    | 필수                            |
| description         | Text, nullable                 |                                 |
| video_path          | String(500)                    | 저장된 비디오 파일명 (UUID.ext) |
| thumbnail_path      | String(500), nullable          | 저장된 썸네일 파일명            |
| category            | String(50), nullable           | 미사용 가능                     |
| duration            | Integer, nullable              |                                 |
| views               | Integer, default 0             |                                 |
| likes               | Integer, default 0             |                                 |
| user_id             | Integer, FK(users.id), CASCADE |                                 |
| created_at          | DateTime                       |                                 |
| updated_at          | DateTime                       |                                 |
| video_public_id     | String(255), nullable          |                                 |
| thumbnail_public_id | String(255), nullable          |                                 |

- **video_path / thumbnail_path**: 실제 파일은 `config["VIDEO_FOLDER"]`, `config["THUMBNAIL_FOLDER"]` 아래에 저장되며, DB에는 **파일명만** 저장 (예: `a1b2c3d4.mp4`).

## 테이블 생성 시점

`create_app()` 내 `with app.app_context(): db.create_all()` 실행 시, 등록된 모델 기준으로 테이블이 생성된다. `from app import models`로 모델을 로드한 뒤 `create_all()`을 호출하므로 User, Video 테이블이 생성된다.
