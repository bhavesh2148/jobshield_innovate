// ============================================================
// JobShield Chrome Extension — Popup Controller
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  const scanInput = document.getElementById("scan-input");
  const btnScanText = document.getElementById("btn-scan-text");
  const btnScanPage = document.getElementById("btn-scan-page");
  
  const resultsBox = document.getElementById("results-box");
  const resultScore = document.getElementById("result-score");
  const resultBadge = document.getElementById("result-badge");
  const resultAction = document.getElementById("result-action");
  const resultFindings = document.getElementById("result-findings");

  // 1. Check Backend Health
  chrome.runtime.sendMessage({ type: "CHECK_HEALTH" }, (response) => {
    if (response && response.online) {
      statusDot.className = "status-dot online";
      statusText.innerText = "Connected (Port 8000)";
    } else {
      statusDot.className = "status-dot offline";
      statusText.innerText = "Backend Offline";
    }
  });

  // 2. Handle "Scan Text" button
  btnScanText.addEventListener("click", () => {
    const text = scanInput.value.trim();
    if (text.length < 10) {
      alert("Please enter at least 10 characters to analyze.");
      return;
    }

    btnScanText.innerText = "Analyzing...";
    btnScanText.disabled = true;

    chrome.runtime.sendMessage(
      {
        type: "SCAN_PAYLOAD",
        payload: { description: text, title: "Manual Scan", company: "" }
      },
      (response) => {
        btnScanText.innerText = "Scan Text";
        btnScanText.disabled = false;

        if (!response || !response.success) {
          alert(`Analysis error: ${response?.error || "Could not connect to localhost:8000"}`);
          return;
        }

        displayResult(response.data);
      }
    );
  });

  // 3. Handle "Scan Page" button
  btnScanPage.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    btnScanPage.innerText = "Extracting...";
    btnScanPage.disabled = true;

    chrome.scripting.executeScript(
      {
        target: { tabId: tab.id },
        func: () => {
          // Trigger the FAB click on the active page
          const fab = document.getElementById("jobshield-fab-btn");
          if (fab) {
            fab.click();
            return true;
          }
          return false;
        }
      },
      () => {
        btnScanPage.innerText = "Scan Page";
        btnScanPage.disabled = false;
        window.close(); // Close popup so user sees in-page drawer
      }
    );
  });

  // 4. Render Results in Popup
  function displayResult(data) {
    resultsBox.style.display = "flex";

    const score = data.risk_score !== undefined ? data.risk_score : 0;
    const level = (data.risk_level || "LOW").toUpperCase();

    resultScore.innerText = `${score}/100`;
    resultBadge.innerText = `${level} RISK`;

    // Color classes
    const colors = {
      CRITICAL: { color: "#ff0055", bg: "rgba(255, 0, 85, 0.15)", border: "rgba(255, 0, 85, 0.4)" },
      HIGH: { color: "#ff6b00", bg: "rgba(255, 107, 0, 0.15)", border: "rgba(255, 107, 0, 0.4)" },
      MEDIUM: { color: "#ffb800", bg: "rgba(255, 184, 0, 0.15)", border: "rgba(255, 184, 0, 0.4)" },
      LOW: { color: "#00e676", bg: "rgba(0, 230, 118, 0.15)", border: "rgba(0, 230, 118, 0.4)" }
    };

    const scheme = colors[level] || colors.LOW;
    resultScore.style.color = scheme.color;
    resultBadge.style.color = scheme.color;
    resultBadge.style.backgroundColor = scheme.bg;
    resultBadge.style.border = `1px solid ${scheme.border}`;

    resultAction.innerHTML = `<strong>${data.action || "ASSESSMENT"}:</strong> ${data.recommendation || "Review details carefully."}`;

    // Render findings
    const findings = data.unified_findings || [];
    if (findings.length > 0) {
      resultFindings.innerHTML = findings.slice(0, 3).map(f => `
        <div class="finding-item">
          <strong>[${f.severity}]</strong> ${f.title}
        </div>
      `).join('');
    } else {
      resultFindings.innerHTML = `<div class="finding-item" style="color: #00e676;">✓ No deterministic threat findings detected.</div>`;
    }
  }
});
