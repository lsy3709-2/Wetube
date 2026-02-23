/**
 * 관리자 페이지 – 프론트 전용. DB·백엔드 없음.
 */

(function () {
  const STORAGE_KEY = 'wetube_admin_logged_in';

  // 관리자 로그인 상태 확인
  function isAdminLoggedIn() {
    return sessionStorage.getItem(STORAGE_KEY) === '1';
  }

  function applyUI() {
    const isLoggedIn = isAdminLoggedIn();
    const adminPage = document.querySelector('[data-admin-logged-in-only]');
    const loggedOutPage = document.querySelector('[data-admin-logged-out-only]');

    if (isLoggedIn) {
      document.body.classList.add('is-admin-logged-in');
      if (adminPage) adminPage.style.display = 'block';
      if (loggedOutPage) loggedOutPage.style.display = 'none';
    } else {
      document.body.classList.remove('is-admin-logged-in');
      if (adminPage) adminPage.style.display = 'none';
      if (loggedOutPage) loggedOutPage.style.display = 'block';
    }
  }

  // 로그아웃
  const logoutBtn = document.getElementById('admin-logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function () {
      if (confirm('관리자 페이지에서 로그아웃하시겠습니까?')) {
        sessionStorage.removeItem(STORAGE_KEY);
        sessionStorage.removeItem('wetube_admin_user');
        window.location.href = '/auth/login';
      }
    });
  }

  // 관리 메뉴 카드 클릭 (href="#" 인 경우만 알림)
  const menuCards = document.querySelectorAll('.admin-menu-card');
  menuCards.forEach(function (card) {
    card.addEventListener('click', function (e) {
      const href = card.getAttribute('href');
      if (!href || href === '#') {
        e.preventDefault();
        const menu = this.dataset.menu || '관리';
        alert('프론트엔드 전용입니다. "' + menu + '" 관리 기능은 추후 구현됩니다.');
      }
    });
  });

  // 초기 UI 적용
  applyUI();
})();
