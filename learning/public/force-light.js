/**
 * Lock light before React mounts. Chainlit uses next-themes with storageKey "vite-ui-theme"
 * (not "themeVariant"); until server config arrives, missing storage falls back to "system"
 * → dark flash on OS dark mode.
 */
(function () {
  const STORAGE_KEY = "vite-ui-theme";

  function applyLight() {
    try {
      localStorage.setItem(STORAGE_KEY, "light");
    } catch (e) {
      /* ignore */
    }
    document.documentElement.classList.remove("dark");
    document.documentElement.style.colorScheme = "light";
  }

  applyLight();
  document.addEventListener("DOMContentLoaded", applyLight);
  window.addEventListener("load", function () {
    applyLight();
    setTimeout(applyLight, 500);
  });
})();
