// Small global JS for FocusFlow pages
(function () {
  // Soft press animation for buttons
  document.querySelectorAll(".btn-primary, .btn-secondary, .btn-ghost").forEach(btn => {
    btn.addEventListener("mousedown", () => btn.style.transform = "translateY(1px)");
    btn.addEventListener("mouseup", () => btn.style.transform = "");
    btn.addEventListener("mouseleave", () => btn.style.transform = "");
  });
  console.log("FocusFlow base JS loaded");
})();