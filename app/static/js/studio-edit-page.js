/**
 * Studio 영상 수정 페이지 – 수정(저장) / 삭제 연동.
 * 저장: 중복 제출 방지(버튼 비활성화). 삭제: 확인창 후 제출, 중복 클릭 방지.
 */

(function () {
  const MAX_THUMBNAIL_SIZE = 5 * 1024 * 1024; // 5MB

  // 로그인 미연동: 편집 시 서버에서 config.DEFAULT_USER_ID 사용
  const form = document.getElementById('edit-form');
  const thumbnailInput = document.getElementById('edit-thumbnail');
  const thumbnailPlaceholder = document.getElementById('edit-thumbnail-placeholder');
  const thumbnailImg = document.getElementById('edit-thumbnail-img');
  const thumbnailRemove = document.getElementById('edit-thumbnail-remove');
  const titleInput = document.getElementById('edit-title');
  const descriptionInput = document.getElementById('edit-description');
  const msgEl = document.getElementById('edit-msg');
  const submitBtn = document.getElementById('edit-submit-btn');
  const deleteBtn = document.getElementById('edit-delete-btn');

  // 썸네일 선택
  if (thumbnailInput) {
    thumbnailInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (file) {
        if (file.size > MAX_THUMBNAIL_SIZE) {
          if (msgEl) {
            msgEl.textContent = '썸네일 파일 크기는 5MB 이하여야 합니다.';
            msgEl.className = 'auth-msg auth-msg--error is-visible';
          }
          thumbnailInput.value = '';
          return;
        }

        if (!file.type.startsWith('image/')) {
          if (msgEl) {
            msgEl.textContent = '이미지 파일만 선택할 수 있습니다.';
            msgEl.className = 'auth-msg auth-msg--error is-visible';
          }
          thumbnailInput.value = '';
          return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
          if (thumbnailImg) {
            thumbnailImg.src = e.target.result;
            thumbnailImg.style.display = 'block';
          }
          if (thumbnailPlaceholder) thumbnailPlaceholder.style.display = 'none';
          if (thumbnailRemove) thumbnailRemove.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });

    // 썸네일 제거
    if (thumbnailRemove) {
      thumbnailRemove.addEventListener('click', function () {
        thumbnailInput.value = '';
        if (thumbnailImg) {
          thumbnailImg.src = '';
          thumbnailImg.style.display = 'none';
        }
        if (thumbnailPlaceholder) thumbnailPlaceholder.style.display = 'flex';
        thumbnailRemove.style.display = 'none';
      });
    }
  }

  // 수정 폼(저장): submit 리스너 없음 → 브라우저 네이티브 제출만 사용 (테이블 미반영 방지).
  // 제목은 input required 로 필수 검사.

  // 삭제 폼 – 확인창 후 제출, 중복 클릭 방지
  const deleteForm = document.getElementById('delete-form');
  if (deleteForm && deleteBtn) {
    deleteForm.addEventListener('submit', function (e) {
      e.preventDefault();
      if (deleteBtn.disabled) return;
      if (!confirm('정말 삭제하시겠습니까?\n삭제된 동영상은 복구할 수 없습니다.')) return;
      deleteBtn.disabled = true;
      deleteBtn.textContent = '삭제 중...';
      deleteForm.submit();
    });
  }

  // 문자 수 카운터
  if (titleInput) {
    titleInput.addEventListener('input', function () {
      const len = this.value.length;
      const hint = this.nextElementSibling;
      if (hint && hint.classList.contains('form-hint')) {
        hint.textContent = len + '/100자';
      }
    });
  }

  if (descriptionInput) {
    descriptionInput.addEventListener('input', function () {
      const len = this.value.length;
      const hint = this.nextElementSibling;
      if (hint && hint.classList.contains('form-hint')) {
        hint.textContent = len + '/5000자';
      }
    });
  }
})();
