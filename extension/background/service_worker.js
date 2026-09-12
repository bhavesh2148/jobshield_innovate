// ============================================================
// JobShield Chrome Extension — Background Service Worker (Manifest V3)
// ============================================================

const JOBSHIELD_API_BASE = "http://127.0.0.1:8000";

// Register Context Menu upon extension installation
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "jobshield-scan-selection",
    title: "🛡️ Scan Selection with JobShield",
    contexts: ["selection"]
  });
  console.log("[JobShield] Service worker initialized & context menus created.");
});

// Handle Context Menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "jobshield-scan-selection" && info.selectionText) {
    const selectedText = info.selectionText.trim();
    if (selectedText.length < 5) {
      notifyTab(tab.id, {
        type: "JOBSHIELD_ERROR",
        message: "Selected text is too short to analyze (minimum 5 characters)."
      });
      return;
    }

    notifyTab(tab.id, { type: "JOBSHIELD_SCAN_STARTED", text: selectedText });

    try {
      const response = await fetch(`${JOBSHIELD_API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: selectedText,
          title: "Selected Web Content",
          company: ""
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || errorData.detail || `Server returned ${response.status}`);
      }

      const result = await response.json();
      notifyTab(tab.id, {
        type: "JOBSHIELD_SCAN_RESULT",
        payload: result,
        analyzedText: selectedText
      });

    } catch (err) {
      console.error("[JobShield] Scan error:", err);
      notifyTab(tab.id, {
        type: "JOBSHIELD_ERROR",
        message: `Failed to connect to JobShield backend at ${JOBSHIELD_API_BASE}. Make sure the FastAPI server is running.`
      });
    }
  }
});

// Helper to safely message the active tab
function notifyTab(tabId, message) {
  if (!tabId) return;
  chrome.tabs.sendMessage(tabId, message).catch((err) => {
    // If content script is not yet injected or tab closed, log gently
    console.warn("[JobShield] Could not message tab:", err.message);
  });
}

// Listen for messages from popup or content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "CHECK_HEALTH") {
    fetch(`${JOBSHIELD_API_BASE}/health`)
      .then(res => res.json())
      .then(data => sendResponse({ online: true, data }))
      .catch(err => sendResponse({ online: false, error: err.message }));
    return true; // Keep channel open for async response
  }

  if (request.type === "SCAN_PAYLOAD") {
    fetch(`${JOBSHIELD_API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request.payload)
    })
      .then(res => {
        if (!res.ok) return res.json().then(e => Promise.reject(e));
        return res.json();
      })
      .then(data => sendResponse({ success: true, data }))
      .catch(err => sendResponse({ success: false, error: err.message || JSON.stringify(err) }));
    return true; // Keep channel open
  }
});
