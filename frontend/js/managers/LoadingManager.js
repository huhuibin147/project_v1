// 加载管理器 - 资源加载状态反馈

const LoadingManager = (() => {
  let loadingCount = 0;
  let overlay = null;
  let textEl = null;
  let initialized = false;

  function init() {
    if (initialized) return;

    overlay = document.createElement("div");
    overlay.id = "loading-overlay";
    overlay.className = "hidden";
    overlay.innerHTML = `
      <div class="loading-spinner"></div>
      <div class="loading-text">加载中...</div>
    `;
    
    document.body.appendChild(overlay);
    textEl = overlay.querySelector(".loading-text");
    initialized = true;
  }

  function startLoading(message = "加载中...") {
    if (!initialized) init();
    
    loadingCount++;
    
    if (overlay) {
      overlay.classList.remove("hidden");
      if (textEl) {
        textEl.textContent = message;
      }
    }
  }

  function finishLoading() {
    loadingCount--;
    
    if (loadingCount <= 0) {
      loadingCount = 0;
      
      if (overlay) {
        overlay.classList.add("hidden");
      }
    }
  }

  function updateProgress(current, total, message = "加载中...") {
    if (textEl) {
      const percent = Math.round((current / total) * 100);
      textEl.textContent = `${message} ${percent}%`;
    }
  }

  function isLoading() {
    return loadingCount > 0;
  }

  function getLoadingCount() {
    return loadingCount;
  }

  return {
    init,
    startLoading,
    finishLoading,
    updateProgress,
    isLoading,
    getLoadingCount
  };
})();
