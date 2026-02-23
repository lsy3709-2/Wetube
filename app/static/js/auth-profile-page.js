/**
 * 회원정보 수정 페이지 – Flask 백엔드 연결.
 * @login_required로 미로그인 시 서버에서 /auth/login으로 리다이렉트.
 * 폼은 POST /auth/profile 으로 제출.
 */

(function () {
  const form = document.getElementById('profile-form');
  const msgEl = document.getElementById('profile-msg');
  const imageInput = document.getElementById('profile-image-input');
  const imagePreview = document.getElementById('profile-image-preview');
  const imagePlaceholder = document.getElementById('profile-image-placeholder');
  const imageRemove = document.getElementById('profile-image-remove');

  if (!form) return;

  // 프로필 이미지 미리보기
  if (imageInput && imagePreview && imagePlaceholder && imageRemove) {
    imageInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (file) {
        // 파일 크기 확인 (5MB 제한)
        if (file.size > 5 * 1024 * 1024) {
          alert('파일 크기는 5MB 이하여야 합니다.');
          imageInput.value = '';
          return;
        }

        // 이미지 파일인지 확인
        if (!file.type.startsWith('image/')) {
          alert('이미지 파일만 선택할 수 있습니다.');
          imageInput.value = '';
          return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
          imagePreview.src = e.target.result;
          imagePreview.style.display = 'block';
          imagePlaceholder.style.display = 'none';
          imageRemove.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });

    // 프로필 이미지 제거
    imageRemove.addEventListener('click', function () {
      imageInput.value = '';
      imagePreview.src = '';
      imagePreview.style.display = 'none';
      imagePlaceholder.style.display = 'flex';
      imageRemove.style.display = 'none';
    });
  }

  form.addEventListener('submit', function (e) {
    if (!msgEl) return;

    // 새 비밀번호 변경 시 클라이언트 검증
    const newPass = (form.querySelector('[name="new_password"]') || {}).value || '';
    const newPassConfirm = (form.querySelector('[name="new_password_confirm"]') || {}).value || '';

    if (newPass && newPass !== newPassConfirm) {
      e.preventDefault();
      msgEl.textContent = '새 비밀번호와 확인이 일치하지 않습니다.';
      msgEl.className = 'auth-msg auth-msg--error is-visible';
      return;
    }

    // 검증 통과 시 폼이 서버로 제출됨 (프로필 이미지는 추후 백엔드 구현)
  });
})();
