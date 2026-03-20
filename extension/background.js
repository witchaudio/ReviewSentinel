// Service worker: set default API endpoint on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.get("apiEndpoint", (data) => {
    if (!data.apiEndpoint) {
      chrome.storage.sync.set({ apiEndpoint: "http://localhost:8000" });
    }
  });
});

// Proxy API calls from content scripts to avoid mixed-content blocks.
// Content scripts on HTTPS Amazon pages cannot fetch HTTP localhost directly.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type !== "SCORE_BATCH") return false;

  const { endpoint, payload } = msg;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);

  fetch(`${endpoint}/score/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviews: payload }),
    signal: controller.signal,
  })
    .then((r) => {
      clearTimeout(timer);
      return r.ok ? r.json() : Promise.reject();
    })
    .then((data) => sendResponse({ ok: true, results: data.results }))
    .catch(() => { clearTimeout(timer); sendResponse({ ok: false }); });

  return true; // keep message channel open for async response
});
