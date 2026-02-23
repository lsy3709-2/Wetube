/**
 * WeTube – 라이트/다크 모드 토글
 * localStorage에 설정 저장
 */

(function () {
  const STORAGE_KEY = 'wetube_theme';

  function getTheme() {
    return localStorage.getItem(STORAGE_KEY) || 'dark';
  }

  function setTheme(theme) {
    localStorage.setItem(STORAGE_KEY, theme);
    document.documentElement.classList.toggle('theme-light', theme === 'light');
  }

  function toggleTheme() {
    const current = getTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
  }

  // 초기 적용
  setTheme(getTheme());

  // 버튼 클릭
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', toggleTheme);
  }
})();
