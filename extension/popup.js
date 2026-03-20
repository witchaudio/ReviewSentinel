const endpointInput = document.getElementById("endpoint");
const saveBtn = document.getElementById("save");
const statusEl = document.getElementById("status");

function setStatus(msg, type) {
  statusEl.textContent = msg;
  statusEl.className = "status-" + type;
}

async function ping(endpoint) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 4000);
  try {
    const resp = await fetch(endpoint + "/health", { signal: controller.signal });
    clearTimeout(timer);
    return resp.ok;
  } catch {
    clearTimeout(timer);
    return false;
  }
}

// Load saved endpoint on open
chrome.storage.sync.get("apiEndpoint", async (data) => {
  const ep = data.apiEndpoint || "http://localhost:8000";
  endpointInput.value = ep;
  setStatus("Checking connection…", "checking");
  const ok = await ping(ep);
  setStatus(ok ? "Connected" : "API offline — start the server", ok ? "ok" : "err");
});

saveBtn.addEventListener("click", async () => {
  const ep = endpointInput.value.trim().replace(/\/$/, "");
  if (!ep) return;
  setStatus("Saving…", "checking");
  chrome.storage.sync.set({ apiEndpoint: ep }, async () => {
    const ok = await ping(ep);
    setStatus(ok ? "Saved — connected" : "Saved — API offline", ok ? "ok" : "err");
  });
});
