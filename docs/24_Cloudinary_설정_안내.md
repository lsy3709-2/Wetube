# Cloudinary 업로드 설정 안내

동영상과 썸네일을 Cloudinary 서버에 업로드하려면 아래 설정을 진행하세요.

## 1. Cloudinary 계정 및 API 키 확인

1. [Cloudinary 콘솔](https://console.cloudinary.com)에 로그인
2. **Dashboard**에서 다음 값을 확인:
   - **Cloud name**
   - **API Key**
   - **API Secret** (Show 클릭 후 복사)

## 2. .env 파일 설정

프로젝트 루트(`ch05`)에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```env
CLOUDINARY_CLOUD_NAME=여기에_cloud_name_입력
CLOUDINARY_API_KEY=여기에_api_key_입력
CLOUDINARY_API_SECRET=여기에_api_secret_입력
```

### 예시 (.env.example 복사 후 수정)

```bash
# Windows PowerShell
copy .env.example .env

# 이후 .env 파일을 열어 실제 값으로 수정
```

### .env 파일 예시

```env
CLOUDINARY_CLOUD_NAME=mycloud123
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcdefghijklmnopqrstuvwxyz12
```

## 3. 동작 방식

| 환경 변수 | 동작 |
|-----------|------|
| **설정됨** | Studio 업로드 시 동영상·썸네일을 Cloudinary에 업로드하고, `secure_url`을 DB의 `video_url`, `thumbnail_url`에 저장 |
| **미설정** | 기존처럼 로컬 `uploads/` 폴더에 저장 (`video_path`, `thumbnail_path` 사용) |

## 4. DB 스키마

Cloudinary 사용 시 다음 컬럼이 사용됩니다:

- `video_url`: 비디오 Cloudinary secure_url
- `thumbnail_url`: 썸네일 Cloudinary secure_url
- `video_public_id`: 삭제 시 Cloudinary 리소스 제거용
- `thumbnail_public_id`: 삭제 시 Cloudinary 리소스 제거용

새 컬럼(`video_url`, `thumbnail_url`)은 앱 실행 시 자동으로 추가됩니다.

## 5. 보안 참고

- `.env` 파일은 `.gitignore`에 포함해 Git에 커밋하지 마세요.
- API Secret은 외부에 노출되지 않도록 관리하세요.
- Cloudinary 무료 플랜에는 일일 변환·저장 한도가 있습니다.
