(function () {
  const refreshBtn = document.getElementById("refresh-btn");
  const feed = document.getElementById("feed");

  if (!refreshBtn) return;

  refreshBtn.addEventListener("click", async () => {
    if (!feed) return;
    refreshBtn.disabled = true;

    try {
      // Demo: light shimmer effect; in the next step we’ll replace this with HTMX/Fetch to your JSON endpoint.
      feed.style.opacity = 0.6;
      setTimeout(() => (feed.style.opacity = 1), 300);
    } finally {
      refreshBtn.disabled = false;
    }
  });

  console.log("FocusFlow dashboard JS ready");
})();