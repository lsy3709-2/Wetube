/**
 * 관리자 데이터베이스 관리 페이지 – 프론트 전용.
 */

(function () {
  const STORAGE_KEY = 'wetube_admin_logged_in';

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

  // 백업
  var backupBtn = document.getElementById('btn-backup');
  if (backupBtn) {
    backupBtn.addEventListener('click', function () {
      alert('프론트엔드 전용입니다. 백업 기능은 추후 구현됩니다.');
    });
  }

  // 로그아웃
  var logoutBtn = document.getElementById('admin-logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function () {
      if (confirm('관리자 페이지에서 로그아웃하시겠습니까?')) {
        sessionStorage.removeItem(STORAGE_KEY);
        sessionStorage.removeItem('wetube_admin_user');
        window.location.href = '/auth/login';
      }
    });
  }

  applyUI();
})();
