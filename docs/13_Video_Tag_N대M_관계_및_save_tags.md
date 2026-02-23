# Video-Tag N:M 관계 및 save_tags 메서드

## 개요

`table.sql`의 `tags`, `video_tags` 테이블을 기반으로 Video 모델과 Tag 모델 간 N:M(다대다) 관계를 설정하고, 콤마로 구분된 태그 문자열을 파싱해 비디오에 연결하는 `save_tags()` 메서드를 구현했다.

---

## 1. 테이블 구조 (table.sql 참고)

### tags

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, 자동증가 |
| name | VARCHAR(50) | 태그명, UNIQUE |
| created_at | TIMESTAMP | 생성 시각 |

### video_tags (중간 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| video_id | INTEGER | FK → videos.id, PK 일부 |
| tag_id | INTEGER | FK → tags.id, PK 일부 |
| created_at | TIMESTAMP | 생성 시각 |

---

## 2. 구현된 모델

### Tag 모델 (`app/models/tag.py`)

```python
class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Video 모델 – video_tags 중간 테이블 (`app/models/video.py`)

```python
video_tags = db.Table(
    "video_tags",
    db.Column("video_id", db.Integer, db.ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow),
)
```

### Video 모델 – N:M 관계

```python
tags = db.relationship(
    "Tag",
    secondary=video_tags,
    backref=db.backref("videos", lazy="dynamic"),
    lazy="select",
)
```

- `Video.tags`: 해당 비디오에 연결된 Tag 목록
- `Tag.videos`: 해당 태그가 붙은 Video 쿼리 (동적 로딩)

---

## 3. save_tags() 메서드

### 시그니처

```python
def save_tags(self, tag_string, commit=True):
```

### 동작

1. **입력 파싱**: `"태그1, 태그2, 태그3"` → `["태그1", "태그2", "태그3"]`
2. **정규화**: 각 태그 앞뒤 공백 제거
3. **길이 검증**: 50자 초과 태그는 제외
4. **Tag 조회/생성**: `Tag.query.filter_by(name=name).first()` → 없으면 `Tag(name=name)` 생성
5. **연결 교체**: 해당 Video의 기존 태그를 새 태그 목록으로 교체
6. **커밋**: `commit=True`이면 `db.session.commit()` 실행

### 특수 입력 처리

| 입력 | 처리 |
|------|------|
| `None`, 빈 문자열 | 태그 목록 비움 |
| `"태그1,  태그2 , 태그3"` | 공백 제거 후 3개 태그로 처리 |
| 50자 초과 태그 | 해당 태그만 제외 |
| 기존 동일 이름 태그 | 재사용 (중복 생성 안 함) |

---

## 4. 사용 예시

```python
from app.models import Video, Tag

# 비디오에 태그 연결 (자동 commit)
video = Video.query.get(1)
video.save_tags("Python, Flask, 튜토리얼")

# 트랜잭션 내에서 commit 제어
video.save_tags("태그1, 태그2", commit=False)
db.session.commit()

# 태그 조회
video.tags          # [Tag(...), Tag(...), ...]
video.tags[0].name  # "Python"

# 태그로 비디오 검색
tag = Tag.query.filter_by(name="Flask").first()
tag.videos.all()    # 해당 태그가 붙은 비디오 목록
```

---

## 5. 모델 내보내기 (`app/models/__init__.py`)

```python
from app.models.tag import Tag
from app.models.user import User
from app.models.video import Video

__all__ = ["User", "Video", "Tag"]
```

---

## 6. 주의사항

- `video_tags` 테이블이 없으면 마이그레이션 또는 `table.sql` 실행 필요
- `save_tags()` 호출 시 `commit=True`가 기본이므로, 여러 작업을 한 트랜잭션으로 묶으려면 `commit=False` 사용 후 별도 `db.session.commit()` 호출
