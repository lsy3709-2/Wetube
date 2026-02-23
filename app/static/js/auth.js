/**
 * WeTube – 로그인 상태 (Flask-Login 세션 기반).
 * base.html에서 서버가 body.is-logged-in, body.is-admin을 설정.
 * 아바타 클릭 시 마이페이지/로그아웃 드롭다운 표시.
 * (하위 호환: 서버 인증이 없을 때만 sessionStorage 폴백)
 */

(function () {
  const STORAGE_KEY = 'wetube_logged_in';

  // 서버에서 이미 로그인 상태를 렌더링했으면 sessionStorage로 덮어쓰지 않음
  if (document.body.classList.contains('is-logged-in')) {
    return;
  }

  // 폴백: 예전 방식(admin 페이지 등) – sessionStorage로 UI 토글
  function applyUI() {
    const loggedIn = sessionStorage.getItem(STORAGE_KEY) === '1';
    const isAdmin = sessionStorage.getItem('wetube_admin_logged_in') === '1';
    document.body.classList.toggle('is-logged-in', loggedIn);
    document.body.classList.toggle('is-admin', isAdmin);
    const userEl = document.getElementById('header-username');
    if (userEl && loggedIn) {
      const u = sessionStorage.getItem('wetube_user') || '';
      userEl.textContent = u ? u.charAt(0).toUpperCase() : '';
    }
    document.querySelectorAll('[data-admin-only]').forEach(function (el) {
      el.style.display = isAdmin ? '' : 'none';
    });
  }

  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn && logoutBtn.tagName === 'BUTTON') {
    logoutBtn.addEventListener('click', function () {
      sessionStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem('wetube_user');
      sessionStorage.removeItem('wetube_admin_logged_in');
      applyUI();
    });
  }

  applyUI();
})();
