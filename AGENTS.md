# AGENTS.md

## Cursor Cloud specific instructions

### Overview

WeTube는 Python/Flask 기반 YouTube 클론 웹 애플리케이션입니다. SQLite(embedded)를 사용하며, 별도의 외부 서비스 없이 단독 실행됩니다.

### Services

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| Flask dev server | `flask run --host=0.0.0.0 --port=5000` | 5000 | `.flaskenv`에서 `FLASK_APP=app` 자동 적용 |

### Running

- **Dev server**: `flask run --host=0.0.0.0 --port=5000` (또는 `python -m app`)
- **Tests**: `python3 -m pytest tests/ -v`
- DB(`instance/wetube.db`)는 첫 실행 시 자동 생성되며 기본 사용자(`default`/`default`)와 관리자(`admin`/`admin1234`)가 자동 시드됩니다.

### Caveats

- `~/.local/bin`이 PATH에 있어야 `flask`, `pytest` 명령이 동작합니다. (`export PATH="$HOME/.local/bin:$PATH"`)
- 테스트 중 일부(약 40건)가 DB 격리 이슈로 실패할 수 있습니다(in-memory SQLite fallback 로직 문제). 이는 기존 코드의 알려진 동작이며 코드 변경 시 regression 여부 판단 기준으로는 172/222 passed를 참고하세요.
- Cloudinary 관련 환경변수 없이도 로컬 `uploads/` 폴더 방식으로 정상 동작합니다.
- 린트 도구(flake8, pylint 등)는 프로젝트에 포함되어 있지 않습니다.
