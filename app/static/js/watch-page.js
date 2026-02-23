/**
 * Watch 페이지 – 프론트 전용. DB·백엔드 없음.
 */

(function () {
  // 로그인 미연동: 시청은 로그인 없이 사용 가능 (업로드와 동일)

  // 좋아요 버튼 – GET /video/<id>/like/status로 초기화, POST /video/<id>/like로 토글
  const likeBtn = document.getElementById('btn-like');
  const videoId = likeBtn && likeBtn.dataset.videoId;

  // 페이지 로드 시: GET /video/<id>/like/status로 현재 좋아요 상태 불러오기
  if (likeBtn && videoId) {
    fetch('/video/' + videoId + '/like/status')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          if (data.is_liked) likeBtn.classList.add('active');
          var countEl = likeBtn.querySelector('.action-count');
          if (countEl) countEl.textContent = data.likes_count;
        }
      })
      .catch(function () { /* 상태 조회 실패 시 초기값 유지 */ });

    likeBtn.addEventListener('click', function () {
      var btn = this;
      if (btn.disabled) return;

      // 비로그인 시 로그인 페이지로 이동
      var body = document.body;
      if (body && !body.classList.contains('is-logged-in')) {
        if (confirm('로그인 후 좋아요를 누를 수 있습니다. 로그인 페이지로 이동할까요?')) {
          window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
        }
        return;
      }

      btn.disabled = true;

      var csrfMeta = document.querySelector('meta[name="csrf-token"]');
      var headers = { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' };
      if (csrfMeta) headers['X-CSRFToken'] = csrfMeta.getAttribute('content');

      fetch('/video/' + videoId + '/like', {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin',
      })
        .then(function (r) {
          // 세션 만료 시 302 리다이렉트 → 로그인 페이지로 이동
          if (r.redirected || r.status === 302) {
            window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
            return null;
          }
          return r.json();
        })
        .then(function (data) {
          if (!data) return;
          if (data.success) {
            data.is_liked ? btn.classList.add('active') : btn.classList.remove('active');
            var countEl = btn.querySelector('.action-count');
            if (countEl) countEl.textContent = data.likes_count;
          } else {
            alert(data.error || '오류가 발생했습니다.');
          }
        })
        .catch(function () { alert('요청 실패'); })
        .finally(function () { btn.disabled = false; });
    });
  }

  // 구독 버튼 (DB 반영)
  const subscribeBtn = document.getElementById('btn-subscribe');
  if (subscribeBtn) {
    subscribeBtn.addEventListener('click', function () {
      const username = this.dataset.channelUsername;
      if (!username) return;

      const btn = this;
      btn.disabled = true;

      var csrfMeta = document.querySelector('meta[name="csrf-token"]');
      var headers = { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' };
      if (csrfMeta) headers['X-CSRFToken'] = csrfMeta.getAttribute('content');

      fetch('/user/' + encodeURIComponent(username) + '/subscribe', {
        method: 'POST',
        headers: headers,
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            if (data.is_subscribed) {
              btn.classList.add('subscribed', 'btn--outline');
              btn.classList.remove('btn--primary');
              btn.textContent = '구독중';
            } else {
              btn.classList.remove('subscribed', 'btn--outline');
              btn.classList.add('btn--primary');
              btn.textContent = '구독';
            }
            // 구독자 수 화면 갱신
            const subsEl = document.getElementById('channel-subs');
            if (subsEl && typeof data.subscriber_count === 'number') {
              subsEl.textContent = '구독자 ' + data.subscriber_count + '명';
            }
          } else {
            alert(data.error || '오류가 발생했습니다.');
          }
        })
        .catch(function () { alert('요청 실패'); })
        .finally(function () { btn.disabled = false; });
    });
  }

  // 설명 더보기/접기
  const descriptionContent = document.getElementById('description-content');
  const descriptionToggle = document.getElementById('description-toggle');

  if (descriptionContent && descriptionToggle) {
    descriptionToggle.addEventListener('click', function () {
      descriptionContent.classList.toggle('expanded');
      this.textContent = descriptionContent.classList.contains('expanded') ? '간략히' : '더보기';
    });
  }

  // 댓글 입력 – 포커스 시 액션 버튼 표시 (폼 제출은 POST로 처리)
  const commentInput = document.getElementById('comment-input');
  const commentActions = document.getElementById('comment-actions');
  const commentCancel = document.getElementById('comment-cancel');

  if (commentInput && commentActions) {
    commentInput.addEventListener('focus', function () {
      commentActions.style.display = 'flex';
    });
  }

  if (commentCancel && commentInput) {
    commentCancel.addEventListener('click', function () {
      commentInput.value = '';
      commentActions.style.display = 'none';
      commentInput.blur();
    });
  }

  // 답글 버튼 – 클릭 시 답글 폼 표시
  document.querySelectorAll('.comment-reply-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const parentId = this.dataset.parentId;
      const wrap = document.getElementById('reply-form-wrap-' + parentId);
      if (!wrap) return;
      wrap.style.display = wrap.style.display === 'none' ? 'block' : 'none';
    });
  });

  // 답글 취소
  document.querySelectorAll('.reply-cancel').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const parentId = this.dataset.parentId;
      const wrap = document.getElementById('reply-form-wrap-' + parentId);
      if (wrap) wrap.style.display = 'none';
    });
  });

  // 수정 버튼 – 클릭 시 편집 폼 표시
  document.querySelectorAll('.comment-edit-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const commentId = this.dataset.commentId;
      const textEl = document.querySelector('.comment-text[data-comment-id="' + commentId + '"]');
      const formWrap = document.getElementById('edit-form-' + commentId);
      if (!textEl || !formWrap) return;
      textEl.style.display = 'none';
      formWrap.style.display = 'block';
    });
  });

  // 수정 취소
  document.querySelectorAll('.comment-edit-cancel').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const commentId = this.dataset.commentId;
      const textEl = document.querySelector('.comment-text[data-comment-id="' + commentId + '"]');
      const formWrap = document.getElementById('edit-form-' + commentId);
      if (textEl) textEl.style.display = '';
      if (formWrap) formWrap.style.display = 'none';
    });
  });

  // 정렬 버튼
  const sortBtns = document.querySelectorAll('.sort-btn');
  sortBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      sortBtns.forEach(function (b) { b.classList.remove('active'); });
      this.classList.add('active');
    });
  });
})();
