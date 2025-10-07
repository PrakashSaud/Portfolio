/**
 * FocusFlow Analytics Dashboard
 * ------------------------------
 * Fetches conversation + task data and renders interactive charts + summary stats.
 */

document.addEventListener("DOMContentLoaded", () => {
  const colors = {
    blue: "#3b82f6",
    green: "#10b981",
    red: "#ef4444",
    yellow: "#f59e0b",
    gray: "#9ca3af",
  };

  async function fetchJSON(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn("Fetch failed:", e);
      return { results: [] };
    }
  }

  async function loadAnalytics() {
    // Fetch conversations and actions
    const convData = await fetchJSON("/focusflow/api/conversations/");
    const actData = await fetchJSON("/focusflow/api/actions/");

    // --- Summary Counters ---
    const convCount = convData.count ?? convData.results.length ?? 0;
    const taskCount = actData.count ?? actData.results.length ?? 0;

    const uniqueWorkspaces = new Set(convData.results.map((c) => c.workspace)).size;
    const workspaceCount = uniqueWorkspaces || 1;

    let totalSummaries = 0;
    convData.results.forEach((c) => {
      if (c.annotations) {
        totalSummaries += c.annotations.filter((a) => a.kind === "summary").length;
      }
    });

    // Update the counters in the UI
    const statConversations = document.getElementById("statConversations");
    const statTasks = document.getElementById("statTasks");
    const statSummaries = document.getElementById("statSummaries");
    const statWorkspaces = document.getElementById("statWorkspaces");

    if (statConversations) statConversations.textContent = convCount;
    if (statTasks) statTasks.textContent = taskCount;
    if (statSummaries) statSummaries.textContent = totalSummaries;
    if (statWorkspaces) statWorkspaces.textContent = workspaceCount;

    // --- Messages by Source ---
    const bySource = {};
    convData.results.forEach((c) => {
      const src = c.stream || "Unknown";
      bySource[src] = (bySource[src] || 0) + 1;
    });

    const ctxSource = document.getElementById("chartMessagesBySource");
    if (ctxSource) {
      new Chart(ctxSource, {
        type: "doughnut",
        data: {
          labels: Object.keys(bySource),
          datasets: [
            {
              label: "Messages",
              data: Object.values(bySource),
              backgroundColor: [colors.blue, colors.green, colors.yellow, colors.red, colors.gray],
            },
          ],
        },
        options: {
          plugins: { legend: { position: "bottom" } },
        },
      });
    }

    // --- Conversations by Priority ---
    const byPriority = { urgent: 0, action: 0, fyi: 0, spam: 0 };
    convData.results.forEach((c) => {
      const p = c.priority?.toLowerCase();
      if (p && byPriority[p] !== undefined) byPriority[p]++;
    });

    const ctxPriority = document.getElementById("chartConversationsByPriority");
    if (ctxPriority) {
      new Chart(ctxPriority, {
        type: "bar",
        data: {
          labels: Object.keys(byPriority),
          datasets: [
            {
              label: "Conversations",
              data: Object.values(byPriority),
              backgroundColor: [colors.red, colors.yellow, colors.blue, colors.gray],
            },
          ],
        },
        options: {
          scales: {
            y: { beginAtZero: true },
          },
        },
      });
    }

    // --- Task Completion Overview ---
    const taskStatus = { todo: 0, doing: 0, done: 0, dismissed: 0 };
    actData.results.forEach((t) => {
      const s = t.status?.toLowerCase();
      if (s && taskStatus[s] !== undefined) taskStatus[s]++;
    });

    const ctxTasks = document.getElementById("chartTasksCompletion");
    if (ctxTasks) {
      new Chart(ctxTasks, {
        type: "line",
        data: {
          labels: Object.keys(taskStatus),
          datasets: [
            {
              label: "Tasks",
              data: Object.values(taskStatus),
              borderColor: colors.blue,
              backgroundColor: colors.blue + "33",
              tension: 0.4,
              fill: true,
            },
          ],
        },
        options: {
          scales: { y: { beginAtZero: true } },
        },
      });
    }
  }

  // Run analytics loading
  loadAnalytics();
});