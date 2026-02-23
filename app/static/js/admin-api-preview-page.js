/**
 * API 미리보기 페이지 – REST API 연동
 * /api/videos, /api/tags/popular 호출하여 표시
 */
(function () {
  const videosBtn = document.getElementById('btn-load-videos');
  const tagsBtn = document.getElementById('btn-load-tags');
  const videosResult = document.getElementById('api-videos-result');
  const tagsResult = document.getElementById('api-tags-result');

  if (videosBtn && videosResult) {
    videosBtn.addEventListener('click', function () {
      videosResult.innerHTML = '<p class="admin-msg-text">로딩 중...</p>';
      fetch('/api/videos?per_page=5')
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.success) {
            videosResult.innerHTML = '<p class="admin-msg-text auth-msg--error">오류: ' + (data.error || '알 수 없음') + '</p>';
            return;
          }
          var items = data.items || [];
          var meta = data.meta || {};
          var html = '<p class="admin-msg-text">총 ' + (meta.total_items || items.length) + '개 (페이지 ' + (meta.current_page || 1) + '/' + (meta.total_pages || 1) + ')</p>';
          if (items.length) {
            html += '<table class="admin-table"><thead><tr><th>id</th><th>title</th><th>views</th><th>channel</th></tr></thead><tbody>';
            items.forEach(function (v) {
              var ch = (v.channel && v.channel.username) || '-';
              html += '<tr><td>' + (v.id || '') + '</td><td>' + escapeHtml(v.title || '') + '</td><td>' + (v.views || 0) + '</td><td>' + escapeHtml(ch) + '</td></tr>';
            });
            html += '</tbody></table>';
          } else {
            html += '<p class="admin-msg-text">비디오가 없습니다.</p>';
          }
          videosResult.innerHTML = html;
        })
        .catch(function (err) {
          videosResult.innerHTML = '<p class="admin-msg-text auth-msg--error">요청 실패: ' + escapeHtml(String(err)) + '</p>';
        });
    });
  }

  if (tagsBtn && tagsResult) {
    tagsBtn.addEventListener('click', function () {
      tagsResult.innerHTML = '<p class="admin-msg-text">로딩 중...</p>';
      fetch('/api/tags/popular?limit=10')
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.success) {
            tagsResult.innerHTML = '<p class="admin-msg-text auth-msg--error">오류: ' + (data.error || '알 수 없음') + '</p>';
            return;
          }
          var items = data.items || [];
          var html = '<p class="admin-msg-text">' + items.length + '개 태그</p>';
          if (items.length) {
            html += '<table class="admin-table"><thead><tr><th>id</th><th>name</th></tr></thead><tbody>';
            items.forEach(function (t) {
              html += '<tr><td>' + (t.id || '') + '</td><td>#' + escapeHtml(t.name || '') + '</td></tr>';
            });
            html += '</tbody></table>';
          } else {
            html += '<p class="admin-msg-text">태그가 없습니다.</p>';
          }
          tagsResult.innerHTML = html;
        })
        .catch(function (err) {
          tagsResult.innerHTML = '<p class="admin-msg-text auth-msg--error">요청 실패: ' + escapeHtml(String(err)) + '</p>';
        });
    });
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }
})();
