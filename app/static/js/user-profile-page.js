/**
 * 사용자 프로필 페이지 – 프론트 전용.
 */

(function () {
  const subscribeBtn = document.getElementById('btn-subscribe');
  const profileTabs = document.querySelectorAll('.profile-tab');
  const tabContents = document.querySelectorAll('.user-profile-content');

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
          } else {
            alert(data.error || '오류가 발생했습니다.');
          }
        })
        .catch(function () { alert('요청 실패'); })
        .finally(function () { btn.disabled = false; });
    });
  }

  profileTabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      const tabName = this.dataset.tab;

      profileTabs.forEach(function (t) { t.classList.remove('active'); });
      this.classList.add('active');

      tabContents.forEach(function (content) {
        const id = content.id;
        if (id === 'tab-' + tabName) {
          content.style.display = 'block';
        } else {
          content.style.display = 'none';
        }
      });
    });
  });
})();
