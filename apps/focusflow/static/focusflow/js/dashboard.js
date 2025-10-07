/**
 * FocusFlow Dashboard JS
 * -----------------------
 * Fetches live conversations + messages using API endpoints,
 * and updates the dashboard feed dynamically.
 *
 * Safe for local dev: falls back to server-rendered summaries if no API data.
 */

document.addEventListener("DOMContentLoaded", () => {
  const refreshBtn = document.getElementById("refresh-btn");
  const feed = document.getElementById("feed");
  const emptyState = document.querySelector("[data-empty-state]");

  // endpoint definitions (can adjust later)
  const conversationsAPI = "/focusflow/api/conversations/";
  const messagesAPI = "/focusflow/api/messages/";

  async function fetchJSON(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error("Fetch failed:", err);
      return null;
    }
  }

  async function loadDashboard() {
    if (!feed) return;

    feed.innerHTML = `<div class="text-center text-gray-500 py-6 animate-pulse">Loading AI summaries...</div>`;

    const data = await fetchJSON(conversationsAPI);
    if (!data || !data.results || !data.results.length) {
      feed.innerHTML = "";
      if (emptyState) emptyState.classList.remove("hidden");
      return;
    }

    // hide empty state if visible
    if (emptyState) emptyState.classList.add("hidden");

    const itemsHTML = data.results
      .map(
        (conv) => `
        <article class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 shadow-sm hover:shadow-md transition">
          <header class="mb-3">
            <div class="flex justify-between items-center">
              <h3 class="font-semibold text-lg">${conv.subject || "(no subject)"}</h3>
              <span class="text-xs uppercase px-2 py-1 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">${conv.priority}</span>
            </div>
            <p class="text-xs text-gray-500">${conv.workspace || ""} • ${conv.stream || ""}</p>
          </header>

          <div class="text-sm text-gray-700 dark:text-gray-300 line-clamp-4" id="summary-${conv.id}">
            <em>Fetching summary...</em>
          </div>

          <footer class="mt-4 flex justify-between items-center">
            <button data-load-messages="${conv.id}" class="text-sm text-blue-600 hover:underline">View Messages</button>
            <span class="text-xs text-gray-400">${conv.unread_count} unread</span>
          </footer>
        </article>`
      )
      .join("");

    feed.innerHTML = itemsHTML;

    // For each conversation, fetch its AI summary annotation
    data.results.forEach((conv) => {
      fetch(`/focusflow/api/conversations/${conv.id}/`)
        .then((res) => res.json())
        .then((detail) => {
          const summaryDiv = document.getElementById(`summary-${conv.id}`);
          if (!summaryDiv) return;
          const ann = detail.annotations?.find((a) => a.kind === "summary");
          if (ann && ann.content_text) {
            summaryDiv.textContent = ann.content_text;
          } else {
            summaryDiv.textContent = "(no AI summary yet)";
          }
        })
        .catch(() => {});
    });
  }

  // Load when page opens
  loadDashboard();

  // Manual refresh
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadDashboard();
    });
  }

  // Dynamic message preview
  document.body.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("[data-load-messages]");
    if (!btn) return;
    const convId = btn.getAttribute("data-load-messages");
    const msgData = await fetchJSON(`${messagesAPI}?conversation_id=${convId}`);
    if (!msgData || !msgData.results) return;

    const modal = document.createElement("div");
    modal.className =
      "fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4";
    modal.innerHTML = `
      <div class="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full p-6 shadow-xl relative">
        <button class="absolute top-2 right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" data-close-modal>&times;</button>
        <h2 class="text-lg font-semibold mb-3">Messages (${msgData.results.length})</h2>
        <div class="overflow-y-auto max-h-[70vh] space-y-4">
          ${msgData.results
            .map(
              (m) => `
            <div class="border-b border-gray-200 dark:border-gray-700 pb-2">
              <p class="text-sm text-gray-500 mb-1">${m.sender || "Unknown"} • ${m.sent_at}</p>
              <p class="text-gray-800 dark:text-gray-200">${m.text || "(no content)"}</p>
            </div>`
            )
            .join("")}
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    modal.addEventListener("click", (e) => {
      if (e.target.hasAttribute("data-close-modal") || e.target === modal) {
        modal.remove();
      }
    });
  });
});