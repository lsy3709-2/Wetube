/**
 * 로그인 페이지 – Flask 백엔드 연결.
 * 폼이 POST /auth/login 으로 제출되고, 서버에서 검증 후 리다이렉트 또는 에러 렌더.
 * flash 메시지는 base.html에서 표시됨.
 */

(function () {
  const form = document.getElementById('login-form');
  const errorEl = document.getElementById('login-error');

  if (!form) return;

  // 필수 입력 등 클라이언트 검증만. 실제 인증은 서버에서 수행. 에러는 base flash로 표시.
  form.addEventListener('submit', function (e) {
    const loginId = document.getElementById('login-id');
    const password = document.getElementById('login-password');
    if ((!loginId || !loginId.value.trim()) || (!password || !password.value)) {
      e.preventDefault();
      if (errorEl) {
        errorEl.textContent = '아이디/이메일과 비밀번호를 입력해주세요.';
        errorEl.classList.add('is-visible', 'auth-msg--error');
      }
      return;
    }
    // 검증 통과 시 폼이 서버로 제출됨
  });
})();
