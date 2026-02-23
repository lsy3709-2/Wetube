/**
 * Studio 업로드 페이지 – 프론트 전용. DB·백엔드 없음.
 */

(function () {
  const MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024; // 2GB
  const MAX_THUMBNAIL_SIZE = 5 * 1024 * 1024; // 5MB

  // 로그인 미연동: 업로드 시 서버에서 config.DEFAULT_USER_ID 사용
  const form = document.getElementById("upload-form");
  const videoInput = document.getElementById("upload-video");
  const videoArea = document.getElementById("upload-file-area");
  const videoPlaceholder = document.getElementById("upload-file-placeholder");
  const videoSelected = document.getElementById("upload-file-selected");
  const videoName = document.getElementById("upload-file-name");
  const videoSize = document.getElementById("upload-file-size");
  const videoRemove = document.getElementById("upload-file-remove");
  const thumbnailInput = document.getElementById("upload-thumbnail");
  const thumbnailPreview = document.getElementById("upload-thumbnail-preview");
  const thumbnailPlaceholder = document.getElementById(
    "upload-thumbnail-placeholder"
  );
  const thumbnailImg = document.getElementById("upload-thumbnail-img");
  const thumbnailRemove = document.getElementById("upload-thumbnail-remove");
  const titleInput = document.getElementById("upload-title");
  const descriptionInput = document.getElementById("upload-description");
  const msgEl = document.getElementById("upload-msg");
  const submitBtn = document.getElementById("upload-submit-btn");

  function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  }

  // 동영상 파일 선택
  if (videoInput && videoArea) {
    videoInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (file) {
        if (file.size > MAX_VIDEO_SIZE) {
          if (msgEl) {
            msgEl.textContent = "동영상 파일 크기는 2GB 이하여야 합니다.";
            msgEl.className = "auth-msg auth-msg--error is-visible";
          }
          videoInput.value = "";
          return;
        }

        if (!file.type.startsWith("video/")) {
          if (msgEl) {
            msgEl.textContent = "동영상 파일만 선택할 수 있습니다.";
            msgEl.className = "auth-msg auth-msg--error is-visible";
          }
          videoInput.value = "";
          return;
        }

        if (videoName) videoName.textContent = file.name;
        if (videoSize) videoSize.textContent = formatFileSize(file.size);
        if (videoPlaceholder) videoPlaceholder.style.display = "none";
        if (videoSelected) videoSelected.style.display = "flex";
        if (msgEl) {
          msgEl.textContent = "";
          msgEl.className = "auth-msg";
        }
      }
    });

    // 파일 제거
    if (videoRemove) {
      videoRemove.addEventListener("click", function () {
        videoInput.value = "";
        if (videoPlaceholder) videoPlaceholder.style.display = "flex";
        if (videoSelected) videoSelected.style.display = "none";
      });
    }

    // 드래그 앤 드롭
    videoArea.addEventListener("dragover", function (e) {
      e.preventDefault();
      videoArea.classList.add("drag-over");
    });

    videoArea.addEventListener("dragleave", function (e) {
      e.preventDefault();
      videoArea.classList.remove("drag-over");
    });

    videoArea.addEventListener("drop", function (e) {
      e.preventDefault();
      videoArea.classList.remove("drag-over");
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        videoInput.files = files;
        videoInput.dispatchEvent(new Event("change"));
      }
    });
  }

  // 썸네일 선택
  if (thumbnailInput && thumbnailPreview) {
    thumbnailInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (file) {
        if (file.size > MAX_THUMBNAIL_SIZE) {
          if (msgEl) {
            msgEl.textContent = "썸네일 파일 크기는 5MB 이하여야 합니다.";
            msgEl.className = "auth-msg auth-msg--error is-visible";
          }
          thumbnailInput.value = "";
          return;
        }

        if (!file.type.startsWith("image/")) {
          if (msgEl) {
            msgEl.textContent = "이미지 파일만 선택할 수 있습니다.";
            msgEl.className = "auth-msg auth-msg--error is-visible";
          }
          thumbnailInput.value = "";
          return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
          if (thumbnailImg) {
            thumbnailImg.src = e.target.result;
            thumbnailImg.style.display = "block";
          }
          if (thumbnailPlaceholder) thumbnailPlaceholder.style.display = "none";
          if (thumbnailRemove) thumbnailRemove.style.display = "block";
        };
        reader.readAsDataURL(file);
      }
    });

    // 썸네일 제거
    if (thumbnailRemove) {
      thumbnailRemove.addEventListener("click", function () {
        thumbnailInput.value = "";
        if (thumbnailImg) {
          thumbnailImg.src = "";
          thumbnailImg.style.display = "none";
        }
        if (thumbnailPlaceholder) thumbnailPlaceholder.style.display = "flex";
        thumbnailRemove.style.display = "none";
      });
    }
  }

  // 폼 제출: 클라이언트 검증 통과 시 서버로 전송
  if (form) {
    form.addEventListener("submit", function (e) {
      const video = videoInput && videoInput.files[0];
      const title = titleInput && titleInput.value.trim();

      if (!video) {
        e.preventDefault();
        if (msgEl) {
          msgEl.textContent = "동영상 파일을 선택해주세요.";
          msgEl.className = "auth-msg auth-msg--error is-visible";
        }
        return;
      }

      if (!title) {
        e.preventDefault();
        if (msgEl) {
          msgEl.textContent = "제목을 입력해주세요.";
          msgEl.className = "auth-msg auth-msg--error is-visible";
        }
        titleInput && titleInput.focus();
        return;
      }

      // 검증 통과 시 서버 제출 (preventDefault 하지 않음)
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "업로드 중...";
      }
    });
  }

  // 문자 수 카운터 (선택)
  if (titleInput) {
    titleInput.addEventListener("input", function () {
      const len = this.value.length;
      const hint = this.nextElementSibling;
      if (hint && hint.classList.contains("form-hint")) {
        hint.textContent = `${len}/100자`;
      }
    });
  }

  if (descriptionInput) {
    descriptionInput.addEventListener("input", function () {
      const len = this.value.length;
      const hint = this.nextElementSibling;
      if (hint && hint.classList.contains("form-hint")) {
        hint.textContent = `${len}/5000자`;
      }
    });
  }
})();
