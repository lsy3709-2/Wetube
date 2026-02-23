/**
 * Studio 페이지 – 프론트 전용. DB·백엔드 없음.
 */

(function () {
  const uploadBtn = document.getElementById('btn-upload');
  const uploadBtnEmpty = document.getElementById('btn-upload-empty');
  const emptyState = document.getElementById('studio-empty');
  const videoList = document.getElementById('studio-video-list');

  // 로그인 미연동: Studio는 로그인 없이 사용 가능 (업로드 시 서버에서 DEFAULT_USER_ID 사용)
  // 업로드 버튼은 링크로 처리 (studio/upload.html로 이동)

  // 동영상 목록 표시/숨김 (샘플 데이터가 있으면 목록 표시)
  if (emptyState && videoList) {
    const hasVideos = document.querySelectorAll('.video-row').length > 0;
    if (hasVideos) {
      emptyState.style.display = 'none';
      videoList.style.display = 'block';
    } else {
      emptyState.style.display = 'block';
      videoList.style.display = 'none';
    }
  }
})();
