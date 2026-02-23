/**
 * 관리자 Query 실행 페이지 – 프론트 전용.
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

  // 샘플 결과 (프론트 전용)
  function getSampleResult(query) {
    var q = (query || '').trim().toUpperCase();
    if (q.indexOf('SELECT') === 0) {
      return '<table class="admin-table"><thead><tr><th>id</th><th>username</th><th>email</th></tr></thead><tbody>' +
        '<tr><td>1</td><td>aaa</td><td>aaa@example.com</td></tr>' +
        '<tr><td>2</td><td>admin</td><td>admin@example.com</td></tr>' +
        '<tr><td>3</td><td>lsye</td><td>lsye@example.com</td></tr>' +
        '</tbody></table><p class="admin-msg-text">3 rows (프론트엔드 샘플 결과)</p>';
    }
    if (q.indexOf('INSERT') === 0 || q.indexOf('UPDATE') === 0 || q.indexOf('DELETE') === 0) {
      return '<p class="admin-msg-text">프론트엔드 전용입니다. 실제 DB 수정은 추후 구현됩니다.</p>';
    }
    return '<p class="admin-msg-text">프론트엔드 전용입니다. 쿼리 실행 기능은 추후 구현됩니다.</p>';
  }

  // 실행
  var executeBtn = document.getElementById('btn-execute');
  var queryInput = document.getElementById('db-query');
  var resultEl = document.getElementById('db-query-result');

  if (executeBtn && resultEl) {
    executeBtn.addEventListener('click', function () {
      var q = (queryInput && queryInput.value.trim()) || '';
      if (!q) {
        resultEl.innerHTML = '<p class="admin-msg-text auth-msg--error">쿼리를 입력해주세요.</p>';
        return;
      }
      resultEl.innerHTML = getSampleResult(q);
    });
  }

  // 초기화
  var clearBtn = document.getElementById('btn-clear');
  if (clearBtn && queryInput) {
    clearBtn.addEventListener('click', function () {
      queryInput.value = '';
      if (resultEl) {
        resultEl.innerHTML = '<p class="admin-msg-text">쿼리를 입력하고 실행 버튼을 클릭하세요. (프론트엔드 전용)</p>';
      }
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
