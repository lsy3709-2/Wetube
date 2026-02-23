# 단위 테스트 – 비디오 검색 (search 라우트)

import pytest

from app import db
from app.models import User, Video


@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저."""
    return db.session.get(User, 1)


@pytest.fixture
def video_with_keyword(app_ctx, user):
    """제목·설명에 '검색키워드' 포함된 비디오."""
    v = Video(
        title="검색키워드가 포함된 영상",
        description="설명에도 검색키워드가 있습니다.",
        video_path="a.mp4",
        user_id=user.id,
        category="education",
        views=10,
        likes=5,
    )
    db.session.add(v)
    db.session.commit()
    return v


@pytest.fixture
def video_title_only(app_ctx, user):
    """제목에 '플라스크', 설명에 '키워드' 포함 (정렬·카테고리 테스트용)."""
    v = Video(
        title="플라스크 튜토리얼",
        description="Python 웹 키워드 프레임워크",
        video_path="b.mp4",
        user_id=user.id,
        category="tech",
        views=100,
        likes=20,
    )
    db.session.add(v)
    db.session.commit()
    return v


@pytest.fixture
def video_description_only(app_ctx, user):
    """설명에만 '데이터베이스' 포함."""
    v = Video(
        title="SQL 기초",
        description="데이터베이스 설계 방법",
        video_path="c.mp4",
        user_id=user.id,
        category="education",
        views=50,
        likes=3,
    )
    db.session.add(v)
    db.session.commit()
    return v


# ----- 기본 동작 -----
def test_search_empty_q_returns_200(client):
    """검색어 없을 때 200, 빈 상태 메시지."""
    resp = client.get("/search")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "검색어를 입력하세요" in text


def test_search_with_q_returns_200(client, app_ctx, video_with_keyword):
    """검색어 있을 때 200."""
    resp = client.get("/search?q=검색키워드")
    assert resp.status_code == 200


# ----- 복합 키워드 검색 (제목·설명) -----
def test_search_matches_title(client, app_ctx, video_title_only):
    """제목에 검색어 포함 시 결과에 포함."""
    resp = client.get("/search?q=플라스크")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "플라스크 튜토리얼" in text


def test_search_matches_description(client, app_ctx, video_description_only):
    """설명에 검색어 포함 시 결과에 포함."""
    resp = client.get("/search?q=데이터베이스")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "SQL 기초" in text


def test_search_no_match(client, app_ctx, video_with_keyword):
    """매칭되는 비디오 없을 때 결과 없음 메시지."""
    resp = client.get("/search?q=매칭안됨키워드xyz")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "동영상 결과가 없습니다" in text


# ----- 카테고리 필터 -----
def test_search_category_filter(client, app_ctx, video_with_keyword, video_title_only):
    """카테고리 선택 시 해당 카테고리만 결과."""
    # education: video_with_keyword만 (제목에 '키워드' 포함)
    resp = client.get("/search?q=키워드&category=education")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "검색키워드가 포함된 영상" in text
    assert "플라스크 튜토리얼" not in text

    # tech: video_title_only만 (제목에 '플라스크' 포함)
    resp = client.get("/search?q=플라스크&category=tech")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "플라스크 튜토리얼" in text
    assert "검색키워드가 포함된 영상" not in text


# ----- 정렬 -----
def test_search_sort_views(client, app_ctx, video_with_keyword, video_title_only):
    """sort=views → 조회수 내림차순."""
    resp = client.get("/search?q=키워드&sort=views")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    # video_title_only(100) > video_with_keyword(10)
    idx_플라스크 = text.find("플라스크 튜토리얼")
    idx_검색키워드 = text.find("검색키워드가 포함된 영상")
    assert idx_플라스크 >= 0 and idx_검색키워드 >= 0
    assert idx_플라스크 < idx_검색키워드


def test_search_sort_latest(client, app_ctx, video_with_keyword, video_title_only):
    """sort=latest(기본) → 최신순."""
    resp = client.get("/search?q=키워드&sort=latest")
    assert resp.status_code == 200


def test_search_sort_popular(client, app_ctx, video_with_keyword, video_title_only):
    """sort=popular → 좋아요·조회수순."""
    resp = client.get("/search?q=키워드&sort=popular")
    assert resp.status_code == 200


# ----- 페이지네이션 -----
def test_search_pagination_per_page_12(client, app_ctx, user):
    """한 페이지당 12개, 2페이지 구성 확인."""
    for i in range(14):
        v = Video(
            title=f"paginate{i}",
            description="test",
            video_path=f"v{i}.mp4",
            user_id=user.id,
        )
        db.session.add(v)
    db.session.commit()

    # page 1: 12개 (search-result-item 클래스 개수)
    resp = client.get("/search?q=paginate")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert text.count("search-result-item") == 12
    assert "1 / 2" in text

    # page 2: 2개
    resp = client.get("/search?q=paginate&page=2")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert text.count("search-result-item") == 2


def test_search_page_less_than_1_uses_1(client, app_ctx, video_with_keyword):
    """page < 1 시 1페이지로 처리."""
    resp = client.get("/search?q=검색키워드&page=0")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "검색키워드가 포함된 영상" in text


def test_search_page_default_is_1(client, app_ctx, video_with_keyword):
    """page 파라미터 없을 때 1페이지."""
    resp = client.get("/search?q=검색키워드")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "검색키워드가 포함된 영상" in text


# ----- 입력값 유지 (q, category, sort) -----
def test_search_preserves_q_in_response(client, app_ctx, video_with_keyword):
    """응답에 검색어(q) 값 유지."""
    resp = client.get("/search?q=검색키워드")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert 'value="검색키워드"' in text or 'value="검색키워드" ' in text


def test_search_preserves_category_sort(client, app_ctx, video_with_keyword):
    """응답에 category, sort 값 유지."""
    resp = client.get("/search?q=검색키워드&category=education&sort=views")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    # 카테고리/정렬 선택 옵션이 selected 되어 있음
    assert "education" in text
    assert "views" in text
