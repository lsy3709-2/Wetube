"""
DB 검증 스크립트 – 테스트 전/후 데이터베이스 상태를 HTML 화면으로 비교.

사용법:
  python scripts/db_verify.py
  python scripts/db_verify.py --scenario views   # 조회수 증가 시나리오만
  python scripts/db_verify.py --scenario subscribe
"""
import argparse
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 검증용 파일 DB 사용 (instance/test_verify.db) – 절대 경로
instance_dir = project_root / "instance"
instance_dir.mkdir(parents=True, exist_ok=True)
TEST_DB_PATH = instance_dir / "test_verify.db"
# Windows 경로 슬래시 통일 (SQLite URI)
TEST_DB_URI = "sqlite:///" + str(TEST_DB_PATH).replace("\\", "/")


def _capture_db_state(db_session):
    """DB 세션의 주요 테이블 데이터를 딕셔너리로 추출."""
    from sqlalchemy import text

    tables = ["users", "videos", "tags", "video_tags", "subscriptions", "comments"]
    state = {}

    for table in tables:
        try:
            result = db_session.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            if rows:
                # Row → dict (SQLAlchemy 2.0 Row._mapping 또는 result.keys())
                try:
                    keys = list(result.keys())
                except Exception:
                    keys = list(rows[0]._mapping.keys()) if hasattr(rows[0], "_mapping") else []
                state[table] = []
                for row in rows:
                    d = dict(zip(keys, row)) if keys else {}
                    for k, v in list(d.items()):
                        if hasattr(v, "isoformat"):
                            d[k] = v.isoformat() if v else None
                    state[table].append(d)
            else:
                state[table] = []
        except Exception as e:
            state[table] = [{"_error": str(e)}]

    return state


def _state_to_html_table(data, title):
    """테이블별 데이터를 HTML 테이블로 렌더링."""
    if not data:
        return "<p>데이터 없음</p>"

    if isinstance(data[0], dict) and "_error" in data[0]:
        return f'<p class="error">{data[0]["_error"]}</p>'

    cols = list(data[0].keys()) if data else []
    html = f'<table><caption>{title}</caption><thead><tr>'
    for c in cols:
        html += f"<th>{c}</th>"
    html += "</tr></thead><tbody>"

    for row in data:
        html += "<tr>"
        for c in cols:
            val = row.get(c, "")
            if val is None:
                val = "<em>NULL</em>"
            else:
                val = str(val)
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def _diff_states(before, after):
    """전/후 상태 차이를 표시할 행 식별 (간단 버전: videos.views 등)."""
    changes = []
    for table in before:
        if table not in after or table in ("users", "tags", "video_tags", "subscriptions"):
            continue
        b_rows = {r.get("id"): r for r in before[table] if "id" in r}
        a_rows = {r.get("id"): r for r in after[table] if "id" in r}
        for vid, a in a_rows.items():
            if vid not in b_rows:
                changes.append((table, vid, "added", None, a))
                continue
            b = b_rows[vid]
            for k in a:
                if b.get(k) != a.get(k):
                    changes.append((table, vid, k, b.get(k), a.get(k)))
    return changes


def run_scenario_views(app):
    """조회수 증가 시나리오: GET /api/videos/<id>."""
    from app import db

    with app.app_context():
        from app.models import User, Video

        user = db.session.get(User, 1)
        if not user:
            raise RuntimeError("User id=1 없음. create_app에서 기본 유저 생성됨.")

        v = Video(
            title="검증용_조회수테스트",
            description="설명",
            video_path="verify.mp4",
            user_id=user.id,
            views=10,
            likes=0,
        )
        db.session.add(v)
        db.session.commit()
        video_id = v.id

        # 전: API 호출 직전
        before = _capture_db_state(db.session)

    client = app.test_client()
    resp = client.get(f"/api/videos/{video_id}")
    assert resp.status_code == 200, f"API 실패: {resp.status_code}"

    with app.app_context():
        after = _capture_db_state(db.session)

    return before, after, "조회수 증가 (GET /api/videos/<id>)", resp.get_json()


def run_scenario_subscribe(app):
    """구독 토글 시나리오 (로그인 필요)."""
    from app import db

    with app.app_context():
        from app.models import User, Video

        u2 = User(username="verify_other", email="verify@ex.com", password_hash="")
        db.session.add(u2)
        db.session.commit()

        v = Video(title="구독테스트", video_path="s.mp4", user_id=u2.id)
        db.session.add(v)
        db.session.commit()

        before = _capture_db_state(db.session)

    client = app.test_client()
    resp = client.post(f"/user/verify_other/subscribe")
    if resp.status_code in (200, 401):  # 401: 로그인 필요 시
        pass
    else:
        raise RuntimeError(f"구독 API 실패: {resp.status_code}")

    with app.app_context():
        after = _capture_db_state(db.session)

    return before, after, "구독 토글 (POST /user/<username>/subscribe)", resp.get_json(silent=True)


def run_default_scenario(app):
    """기본: 조회수 증가 시나리오."""
    return run_scenario_views(app)


def generate_report(before, after, scenario_name, api_response, changes):
    """전/후 비교 HTML 보고서 생성."""
    changes_html = ""
    if changes:
        changes_html = "<h3>변경 내역</h3><ul>"
        for t, vid, k, old_v, new_v in changes[:20]:
            changes_html += f"<li><strong>{t}.id={vid}</strong> {k}: {old_v} → {new_v}</li>"
        changes_html += "</ul>"

    api_html = ""
    if api_response:
        import json

        api_html = f"<h3>API 응답 (일부)</h3><pre>{json.dumps(api_response, indent=2, ensure_ascii=False)[:1500]}...</pre>"

    tables = ["users", "videos", "tags", "video_tags", "subscriptions", "comments"]
    before_section = ""
    after_section = ""
    for t in tables:
        b = before.get(t, [])
        a = after.get(t, [])
        before_section += f'<div class="table-wrap"><h4>{t} (전)</h4>{_state_to_html_table(b, t)}</div>'
        after_section += f'<div class="table-wrap"><h4>{t} (후)</h4>{_state_to_html_table(a, t)}</div>'

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>DB 검증 - 전/후 비교</title>
  <style>
    body {{ font-family: 'Malgun Gothic', sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }}
    h1 {{ color: #e94560; }}
    h2 {{ color: #0f3460; margin-top: 2em; }}
    h3, h4 {{ color: #aaa; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    .table-wrap {{ overflow-x: auto; margin-bottom: 20px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; background: #16213e; }}
    th, td {{ border: 1px solid #0f3460; padding: 6px 8px; text-align: left; }}
    th {{ background: #0f3460; color: #e94560; }}
    tr:nth-child(even) {{ background: #1a1a2e; }}
    .highlight {{ background: #e94560 !important; color: #fff; }}
    caption {{ font-weight: bold; margin-bottom: 8px; color: #e94560; }}
    pre {{ background: #16213e; padding: 12px; overflow-x: auto; font-size: 11px; }}
    .meta {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
    ul {{ line-height: 1.6; }}
  </style>
</head>
<body>
  <h1>DB 검증 리포트 - 전/후 비교</h1>
  <p class="meta">시나리오: {scenario_name} | 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
  <p class="meta">DB 파일: {TEST_DB_PATH}</p>

  {changes_html}
  {api_html}

  <h2>테이블별 데이터 비교</h2>
  <div class="grid">
    <div>
      <h3>테스트 전 (Before)</h3>
      {before_section}
    </div>
    <div>
      <h3>테스트 후 (After)</h3>
      {after_section}
    </div>
  </div>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="테스트 DB 전/후 비교 검증")
    parser.add_argument("--scenario", choices=["views", "subscribe"], default="views")
    parser.add_argument("--no-open", action="store_true", help="브라우저 자동 열기 안 함")
    args = parser.parse_args()

    # 검증용 파일 DB로 앱 생성
    prev_uri = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DB_URI

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()  # 이전 검증 DB 삭제 → 깨끗한 상태에서 시작

    try:
        from app import create_app

        app = create_app()
        app.config["TESTING"] = True

        if args.scenario == "subscribe":
            before, after, name, api_resp = run_scenario_subscribe(app)
        else:
            before, after, name, api_resp = run_scenario_views(app)

        changes = _diff_states(before, after)
        html = generate_report(before, after, name, api_resp, changes)

        report_path = project_root / "instance" / "db_verify_report.html"
        report_path.write_text(html, encoding="utf-8")

        print(f"리포트 저장: {report_path}")
        if not args.no_open:
            webbrowser.open(f"file://{report_path.resolve()}")

    finally:
        if prev_uri is not None:
            os.environ["DATABASE_URL"] = prev_uri
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


if __name__ == "__main__":
    main()
