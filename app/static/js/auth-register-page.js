/**
 * 회원가입 페이지 – 서버 폼 제출. 추가 유효성 검사(선택).
 */

(function () {
  const form = document.getElementById('register-form');

  if (!form) return;

  // 클라이언트 측 비밀번호 일치 확인 (서버 검증과 중복이지만 UX 보완)
  form.addEventListener('submit', function (e) {
    const pwd = form.querySelector('[name="password"]');
    const pwdConfirm = form.querySelector('[name="password_confirm"]');
    if (pwd && pwdConfirm && pwd.value !== pwdConfirm.value) {
      e.preventDefault();
      alert('비밀번호와 비밀번호 확인이 일치하지 않습니다.');
      return;
    }
    // 검증 통과 시 폼이 서버로 제출됨
  });
})();
