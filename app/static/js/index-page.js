/**
 * 홈(index) 페이지 – REST API 연동 "더 보기"
 * GET /api/videos 에서 추가 영상 로드
 */
(function () {
  const grid = document.getElementById('video-grid');
  const loadMoreBtn = document.getElementById('btn-load-more');
  if (!grid || !loadMoreBtn) return;

  loadMoreBtn.addEventListener('click', function () {
    const base = grid.dataset.apiBase || '/api/videos';
    const category = grid.dataset.category || 'all';
    const sort = grid.dataset.sort || 'latest';
    const tag = grid.dataset.tag || '';
    const nextPage = parseInt(loadMoreBtn.dataset.nextPage || '2', 10);

    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = '로딩 중...';

    const params = new URLSearchParams({
      page: nextPage,
      per_page: 12,
      sort: sort
    });
    if (category && category !== 'all') params.set('category', category);
    if (tag) params.set('tag', tag);

    fetch(base + '?' + params.toString())
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.success || !data.items) return;
        data.items.forEach(function (v) {
          grid.appendChild(createVideoCard(v));
        });
        // 다음 페이지 정보 업데이트
        var meta = data.meta || {};
        if (meta.has_next) {
          loadMoreBtn.dataset.nextPage = String((meta.current_page || nextPage) + 1);
          loadMoreBtn.disabled = false;
          loadMoreBtn.textContent = '더 보기';
        } else {
          loadMoreBtn.parentElement.style.display = 'none';
        }
      })
      .catch(function () {
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = '더 보기';
        alert('영상을 불러오는데 실패했습니다.');
      });
  });

  function createVideoCard(v) {
    var thumb = v.thumbnail_url
      ? '<img src="' + escapeHtml(v.thumbnail_url) + '" alt="" class="video-card-thumb-img">'
      : '<span>📹</span>';
    var channel = (v.channel && v.channel.username) || 'default';
    var profileUrl = '/user/' + encodeURIComponent(channel);
    var watchUrl = '/watch/' + (v.id || '');
    var tagsHtml = '';
    if (v.tags && v.tags.length) {
      v.tags.slice(0, 3).forEach(function (t) {
        tagsHtml += '<a href="/tag/' + encodeURIComponent(t) + '" class="video-card-tag">#' + escapeHtml(t) + '</a>';
      });
    }
    var card = document.createElement('article');
    card.className = 'video-card';
    card.innerHTML =
      '<a href="' + watchUrl + '" class="video-card-link">' +
        '<div class="video-card-thumb">' + thumb + '</div>' +
        '<h3 class="video-card-title">' + escapeHtml(v.title || '') + '</h3>' +
      '</a>' +
      '<a href="' + profileUrl + '" class="video-card-channel">' + escapeHtml(channel) + '</a>' +
      '<p class="video-card-meta">조회수 ' + (v.views || 0) + '회 · 좋아요 ' + (v.likes || 0) + '</p>' +
      (tagsHtml ? '<div class="video-card-tags">' + tagsHtml + '</div>' : '');
    return card;
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }
})();
