# 단위 테스트 – REST API (api 블루프린트)

import pytest

from app import db
from app.models import Tag, User, Video
from app.routes.api import get_related_videos


# ----- 공통 픽스처 -----
@pytest.fixture
def user(app_ctx):
    """테스트용 기본 유저 (id=1)."""
    return db.session.get(User, 1)


@pytest.fixture
def other_user(app_ctx):
    """다른 사용자 (추천 알고리즘·사용자 API 테스트용)."""
    u = User(username="api_other", email="api_other@example.com", password_hash="")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def video_base(app_ctx, user):
    """기본 비디오 (태그 없음)."""
    v = Video(
        title="API테스트 비디오",
        description="설명입니다",
        video_path="a.mp4",
        user_id=user.id,
        category="tech",
        views=10,
        likes=2,
    )
    db.session.add(v)
    db.session.commit()
    return v


# ===========================================================================
# 1. 비디오 API – GET /api/videos
# ===========================================================================


def test_api_videos_list_returns_json(client, app_ctx, video_base):
    """비디오 목록 API → success, items, meta 포함."""
    resp = client.get("/api/videos")
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    data = resp.get_json()
    assert data["success"] is True
    assert "items" in data
    assert "meta" in data
    assert "total_pages" in data["meta"]
    assert "current_page" in data["meta"]


def test_api_videos_list_pagination(client, app_ctx, user):
    """page, per_page 파라미터 반영."""
    for i in range(5):
        v = Video(title=f"p{i}", video_path=f"p{i}.mp4", user_id=user.id)
        db.session.add(v)
    db.session.commit()

    resp = client.get("/api/videos?page=1&per_page=2")
    data = resp.get_json()
    assert len(data["items"]) == 2
    assert data["meta"]["current_page"] == 1
    assert data["meta"]["per_page"] == 2
    assert data["meta"]["total_items"] == 5
    assert data["meta"]["total_pages"] == 3

    resp2 = client.get("/api/videos?page=2&per_page=2")
    data2 = resp2.get_json()
    assert len(data2["items"]) == 2
    assert data2["meta"]["current_page"] == 2


def test_api_videos_list_page_lt_1_uses_1(client, app_ctx, video_base):
    """page < 1 시 1페이지로 처리."""
    resp = client.get("/api/videos?page=0")
    data = resp.get_json()
    assert data["meta"]["current_page"] == 1


def test_api_videos_list_sort_latest(client, app_ctx, user, video_base):
    """sort=latest(기본) → 최신순."""
    v2 = Video(title="나중", video_path="b.mp4", user_id=user.id)
    db.session.add(v2)
    db.session.commit()

    resp = client.get("/api/videos?per_page=5")
    data = resp.get_json()
    titles = [x["title"] for x in data["items"]]
    assert titles[0] == "나중"


def test_api_videos_list_sort_views(client, app_ctx, user):
    """sort=views → 조회수 내림차순."""
    v1 = Video(title="적음", video_path="v1.mp4", user_id=user.id, views=5)
    v2 = Video(title="많음", video_path="v2.mp4", user_id=user.id, views=100)
    db.session.add_all([v1, v2])
    db.session.commit()

    resp = client.get("/api/videos?sort=views&per_page=5")
    data = resp.get_json()
    titles = [x["title"] for x in data["items"]]
    assert titles[0] == "많음"


def test_api_videos_list_sort_popular(client, app_ctx, user):
    """sort=popular → 좋아요·조회수순."""
    v1 = Video(title="인기낮음", video_path="v1.mp4", user_id=user.id, views=10, likes=1)
    v2 = Video(title="인기높음", video_path="v2.mp4", user_id=user.id, views=50, likes=10)
    db.session.add_all([v1, v2])
    db.session.commit()

    resp = client.get("/api/videos?sort=popular&per_page=5")
    data = resp.get_json()
    titles = [x["title"] for x in data["items"]]
    assert titles[0] == "인기높음"


def test_api_videos_list_category_filter(client, app_ctx, user):
    """category 필터 적용."""
    v1 = Video(title="음악영상", video_path="m.mp4", user_id=user.id, category="music")
    v2 = Video(title="테크영상", video_path="t.mp4", user_id=user.id, category="tech")
    db.session.add_all([v1, v2])
    db.session.commit()

    resp = client.get("/api/videos?category=music&per_page=10")
    data = resp.get_json()
    titles = [x["title"] for x in data["items"]]
    assert "음악영상" in titles
    assert "테크영상" not in titles


def test_api_videos_list_search(client, app_ctx, video_base):
    """search 파라미터 → 제목/설명 검색."""
    resp = client.get("/api/videos?search=API테스트")
    data = resp.get_json()
    assert len(data["items"]) >= 1
    assert any(x["title"] == "API테스트 비디오" for x in data["items"])

    resp2 = client.get("/api/videos?search=매칭안됨xyz999")
    data2 = resp2.get_json()
    assert len(data2["items"]) == 0


def test_api_videos_list_item_structure(client, app_ctx, video_base):
    """items 각 요소에 id, title, channel, tags 등 포함."""
    resp = client.get("/api/videos?per_page=1")
    data = resp.get_json()
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert "id" in item
    assert "title" in item
    assert "views" in item
    assert "likes" in item
    assert "channel" in item
    assert "username" in item["channel"]
    assert "tags" in item
    assert "video_url" in item
    assert "thumbnail_url" in item


# ===========================================================================
# 2. 비디오 API – GET /api/videos/<id>
# ===========================================================================


def test_api_video_detail_returns_200(client, app_ctx, video_base):
    """비디오 상세 API → item, related_videos 포함."""
    resp = client.get(f"/api/videos/{video_base.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["item"]["id"] == video_base.id
    assert data["item"]["title"] == video_base.title
    assert "related_videos" in data


def test_api_video_detail_returns_404(client):
    """존재하지 않는 비디오 → 404."""
    resp = client.get("/api/videos/99999")
    assert resp.status_code == 404


def test_api_video_detail_increments_views(client, app_ctx, video_base):
    """상세 조회 시 조회수 1 증가."""
    assert video_base.views == 10
    client.get(f"/api/videos/{video_base.id}")

    updated = db.session.get(Video, video_base.id)
    assert updated.views == 11

    client.get(f"/api/videos/{video_base.id}")
    updated = db.session.get(Video, video_base.id)
    assert updated.views == 12


def test_api_video_detail_excludes_self_from_related(client, app_ctx, user, video_base):
    """관련 동영상에 현재 비디오 미포함."""
    # 비디오 1개만 있을 때
    resp = client.get(f"/api/videos/{video_base.id}")
    data = resp.get_json()
    related_ids = [x["id"] for x in data["related_videos"]]
    assert video_base.id not in related_ids


# ===========================================================================
# 3. get_related_videos 알고리즘
# ===========================================================================


def test_get_related_videos_empty_when_video_not_found(app_ctx):
    """비디오 없으면 빈 리스트."""
    result = get_related_videos(99999)
    assert result == []


def test_get_related_videos_same_tag_priority(app_ctx, user):
    """1순위: 같은 태그 비디오 우선."""
    v1 = Video(title="현재", video_path="v1.mp4", user_id=user.id, category="a")
    v2 = Video(title="같은태그", video_path="v2.mp4", user_id=user.id, category="b")
    v3 = Video(title="다른태그", video_path="v3.mp4", user_id=user.id, category="a")
    db.session.add_all([v1, v2, v3])
    db.session.commit()
    v1.save_tags("공통태그")
    v2.save_tags("공통태그")
    v3.save_tags("다른태그")

    related = get_related_videos(v1.id, limit=5)
    ids = [x.id for x in related]
    assert v2.id in ids  # 같은 태그
    assert v1.id not in ids  # 자신 제외
    # 같은 태그가 먼저 와야 함 (v2가 v3보다 우선)
    idx_v2 = ids.index(v2.id) if v2.id in ids else 999
    idx_v3 = ids.index(v3.id) if v3.id in ids else 999
    assert idx_v2 <= idx_v3


def test_get_related_videos_same_category(app_ctx, user):
    """2순위: 같은 카테고리 (태그 없을 때)."""
    v1 = Video(title="현재", video_path="v1.mp4", user_id=user.id, category="edu")
    v2 = Video(title="같은카테고리", video_path="v2.mp4", user_id=user.id, category="edu")
    db.session.add_all([v1, v2])
    db.session.commit()

    related = get_related_videos(v1.id, limit=5)
    ids = [x.id for x in related]
    assert v2.id in ids
    assert v1.id not in ids


def test_get_related_videos_same_author(app_ctx, user, other_user):
    """3순위: 같은 작성자."""
    v1 = Video(title="현재", video_path="v1.mp4", user_id=user.id)
    v2 = Video(title="같은작성자", video_path="v2.mp4", user_id=user.id)
    v3 = Video(title="다른작성자", video_path="v3.mp4", user_id=other_user.id)
    db.session.add_all([v1, v2, v3])
    db.session.commit()

    related = get_related_videos(v1.id, limit=5)
    ids = [x.id for x in related]
    assert v2.id in ids
    assert v3.id in ids
    assert v1.id not in ids


def test_get_related_videos_limit(app_ctx, user):
    """limit 개수만큼만 반환."""
    v1 = Video(title="현재", video_path="v1.mp4", user_id=user.id)
    db.session.add(v1)
    for i in range(10):
        v = Video(title=f"추가{i}", video_path=f"x{i}.mp4", user_id=user.id)
        db.session.add(v)
    db.session.commit()

    related = get_related_videos(v1.id, limit=3)
    assert len(related) <= 3


def test_get_related_videos_no_duplicates(app_ctx, user):
    """중복 없이 반환."""
    v1 = Video(title="현재", video_path="v1.mp4", user_id=user.id, category="c")
    v2 = Video(title="중복체크", video_path="v2.mp4", user_id=user.id, category="c")
    db.session.add_all([v1, v2])
    db.session.commit()
    v1.save_tags("T")
    v2.save_tags("T")  # 태그+카테고리+작성자 모두 일치

    related = get_related_videos(v1.id, limit=5)
    ids = [x.id for x in related]
    assert len(ids) == len(set(ids))


# ===========================================================================
# 4. 태그 API – GET /api/tags/popular
# ===========================================================================


def test_api_tags_popular_returns_json(client, app_ctx):
    """인기 태그 API → success, items."""
    resp = client.get("/api/tags/popular")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "items" in data


def test_api_tags_popular_limit_param(client, app_ctx, user):
    """limit 파라미터 적용."""
    v = Video(title="t", video_path="t.mp4", user_id=user.id)
    db.session.add(v)
    db.session.commit()
    v.save_tags("A, B, C, D, E")

    resp = client.get("/api/tags/popular?limit=3")
    data = resp.get_json()
    assert len(data["items"]) <= 3


def test_api_tags_popular_item_structure(client, app_ctx, user):
    """각 태그에 id, name 포함."""
    v = Video(title="t", video_path="t.mp4", user_id=user.id)
    db.session.add(v)
    db.session.commit()
    v.save_tags("인기태그")

    resp = client.get("/api/tags/popular")
    data = resp.get_json()
    if data["items"]:
        item = data["items"][0]
        assert "id" in item
        assert "name" in item


# ===========================================================================
# 5. 태그 API – GET /api/tags/<tag_name>/videos
# ===========================================================================


def test_api_tag_videos_returns_200(client, app_ctx, user):
    """태그별 비디오 API → success, tag, items, meta."""
    v = Video(title="태그비디오", video_path="t.mp4", user_id=user.id)
    db.session.add(v)
    db.session.commit()
    v.save_tags("vlog")

    resp = client.get("/api/tags/vlog/videos")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["tag"]["name"] == "vlog"
    assert "items" in data
    assert "meta" in data
    assert any(x["title"] == "태그비디오" for x in data["items"])


def test_api_tag_videos_returns_404_for_unknown_tag(client):
    """존재하지 않는 태그 → 404."""
    resp = client.get("/api/tags/nonexistent_tag_xyz/videos")
    assert resp.status_code == 404


def test_api_tag_videos_latest_order(client, app_ctx, user):
    """태그별 비디오 최신순."""
    v1 = Video(title="먼저", video_path="v1.mp4", user_id=user.id)
    db.session.add(v1)
    db.session.commit()
    v1.save_tags("order")

    v2 = Video(title="나중", video_path="v2.mp4", user_id=user.id)
    db.session.add(v2)
    db.session.commit()
    v2.save_tags("order")

    resp = client.get("/api/tags/order/videos?per_page=5")
    data = resp.get_json()
    titles = [x["title"] for x in data["items"]]
    assert titles[0] == "나중"  # v2가 나중에 생성됐으므로 최신순 첫 번째


def test_api_tag_videos_pagination(client, app_ctx, user):
    """태그별 비디오 페이지네이션."""
    for i in range(5):
        v = Video(title=f"tg{i}", video_path=f"tg{i}.mp4", user_id=user.id)
        db.session.add(v)
        db.session.commit()
        v.save_tags("many")

    resp = client.get("/api/tags/many/videos?page=1&per_page=2")
    data = resp.get_json()
    assert len(data["items"]) == 2
    assert data["meta"]["total_items"] == 5


# ===========================================================================
# 6. 사용자 API – GET /api/users/<username>
# ===========================================================================


def test_api_user_profile_returns_200(client, app_ctx, user, video_base):
    """사용자 프로필 API → success, item, stats."""
    resp = client.get(f"/api/users/{user.username}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["item"]["username"] == user.username
    assert "stats" in data["item"]
    stats = data["item"]["stats"]
    assert "total_views" in stats
    assert "total_likes" in stats
    assert "video_count" in stats
    assert "subscriber_count" in stats


def test_api_user_profile_returns_404(client):
    """존재하지 않는 사용자 → 404."""
    resp = client.get("/api/users/nonexistent_user_xyz")
    assert resp.status_code == 404


def test_api_user_profile_stats_correct(client, app_ctx, user):
    """채널 통계가 DB와 일치."""
    v1 = Video(title="s1", video_path="s1.mp4", user_id=user.id, views=100, likes=5)
    v2 = Video(title="s2", video_path="s2.mp4", user_id=user.id, views=50, likes=3)
    db.session.add_all([v1, v2])
    db.session.commit()

    resp = client.get(f"/api/users/{user.username}")
    data = resp.get_json()
    stats = data["item"]["stats"]
    assert stats["total_views"] == 150
    assert stats["total_likes"] == 8
    assert stats["video_count"] == 2


# ===========================================================================
# 7. 사용자 API – GET /api/users/<username>/videos
# ===========================================================================


def test_api_user_videos_returns_200(client, app_ctx, user, video_base):
    """사용자 비디오 목록 API → success, items, meta."""
    resp = client.get(f"/api/users/{user.username}/videos")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "items" in data
    assert "meta" in data
    assert data["user"]["username"] == user.username
    assert any(x["title"] == "API테스트 비디오" for x in data["items"])


def test_api_user_videos_excludes_other_user(client, app_ctx, user, other_user):
    """다른 사용자 비디오 제외."""
    v = Video(title="다른유저영상", video_path="o.mp4", user_id=other_user.id)
    db.session.add(v)
    db.session.commit()

    resp = client.get(f"/api/users/{user.username}/videos")
    data = resp.get_json()
    titles = [x["title"] for x in data["items"]]
    assert "다른유저영상" not in titles


def test_api_user_videos_pagination(client, app_ctx, user):
    """사용자 비디오 페이지네이션."""
    for i in range(5):
        v = Video(title=f"uv{i}", video_path=f"uv{i}.mp4", user_id=user.id)
        db.session.add(v)
    db.session.commit()

    resp = client.get(f"/api/users/{user.username}/videos?page=1&per_page=2")
    data = resp.get_json()
    assert len(data["items"]) <= 2
    assert data["meta"]["current_page"] == 1
