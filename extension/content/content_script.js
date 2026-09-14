// ============================================================
// JobShield Chrome Extension — Content Script
// ============================================================

(function () {
  console.log("[JobShield] Content script injected.");

  let activeDrawer = null;
  let activeToast = null;

  // ── Platform-Specific DOM Scrapers ─────────────────────────
  function scrapeJobData() {
    const host = window.location.hostname;

    // 1. LinkedIn Job Board Scraper
    if (host.includes("linkedin.com")) {
      const titleEl = document.querySelector(
        ".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title, h1.t-24, .topcard__title"
      );
      const companyEl = document.querySelector(
        ".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name, .topcard__org-name-link"
      );
      const descEl = document.querySelector(
        ".jobs-description__content, #job-details, .show-more-less-html__markup"
      );

      if (descEl && descEl.innerText.trim().length > 20) {
        return {
          title: titleEl ? titleEl.innerText.trim() : "",
          company: companyEl ? companyEl.innerText.trim() : "",
          description: descEl.innerText.trim(),
          source: "LinkedIn"
        };
      }
    }

    // 2. Indeed Job Board Scraper
    if (host.includes("indeed.com")) {
      const titleEl = document.querySelector(
        "h1.jobsearch-JobInfoHeader-title, [data-testid='simpler-jobTitle']"
      );
      const companyEl = document.querySelector(
        "[data-company-name='true'], [data-testid='inlineHeader-companyName']"
      );
      const descEl = document.querySelector("#jobDescriptionText");

      if (descEl && descEl.innerText.trim().length > 20) {
        return {
          title: titleEl ? titleEl.innerText.trim() : "",
          company: companyEl ? companyEl.innerText.trim() : "",
          description: descEl.innerText.trim(),
          source: "Indeed"
        };
      }
    }

    // 3. Glassdoor Scraper
    if (host.includes("glassdoor.com")) {
      const titleEl = document.querySelector("[data-test='jobTitle'], .job-title");
      const companyEl = document.querySelector("[data-test='employerName'], .employer-name");
      const descEl = document.querySelector(".jobDescriptionContent, [data-brandviews='JobDescription']");

      if (descEl && descEl.innerText.trim().length > 20) {
        return {
          title: titleEl ? titleEl.innerText.trim() : "",
          company: companyEl ? companyEl.innerText.trim() : "",
          description: descEl.innerText.trim(),
          source: "Glassdoor"
        };
      }
    }

    // 4. Gmail Scraper
    if (host.includes("mail.google.com")) {
      const activeEmail = document.querySelector(".a3s.aiL");
      if (activeEmail && activeEmail.innerText.trim().length > 20) {
        return {
          title: "Recruitment Email",
          company: "",
          description: activeEmail.innerText.trim(),
          source: "Gmail"
        };
      }
    }

    // Fallback: Selected text or main body text
    const selection = window.getSelection().toString().trim();
    if (selection.length > 20) {
      return {
        title: "Selected Text",
        company: "",
        description: selection,
        source: "User Selection"
      };
    }

    return null;
  }

  // ── Inject Floating Action Button ──────────────────────────
  function injectFloatingActionButton() {
    if (document.getElementById("jobshield-fab-btn")) return;

    const btn = document.createElement("div");
    btn.id = "jobshield-fab-btn";
    btn.className = "jobshield-pulse";
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
      <span>Scan with JobShield</span>
    `;

    btn.addEventListener("click", () => {
      const jobData = scrapeJobData();
      if (!jobData) {
        showToast("⚠️ Highlight suspicious text or navigate to a job post to scan.");
        return;
      }
      triggerScan(jobData);
    });

    document.body.appendChild(btn);
  }

  // ── Trigger API Prediction ─────────────────────────────────
  async function triggerScan(jobData) {
    showToast(`🔍 Analyzing ${jobData.source || "job posting"} with JobShield...`);

    chrome.runtime.sendMessage(
      {
        type: "SCAN_PAYLOAD",
        payload: {
          description: jobData.description,
          title: jobData.title || "",
          company: jobData.company || ""
        }
      },
      (response) => {
        if (!response || !response.success) {
          showToast(`❌ Analysis failed: ${response?.error || "Could not reach local backend at localhost:8000"}`);
          return;
        }
        renderThreatDrawer(response.data, jobData);
      }
    );
  }

  // ── Render Threat Drawer ───────────────────────────────────
  function renderThreatDrawer(data, jobData) {
    if (activeDrawer) activeDrawer.remove();

    const drawer = document.createElement("div");
    drawer.id = "jobshield-drawer";

    const riskLevel = (data.risk_level || "LOW").toUpperCase();
    const riskScore = data.risk_score !== undefined ? data.risk_score : 0;
    const colorClass = `jobshield-${riskLevel.toLowerCase()}`;
    const badgeClass = `jobshield-badge-${riskLevel.toLowerCase()}`;

    // Collect findings & MITRE tags
    const findings = (data.unified_findings || []);
    const mitreTags = [];
    if (data.taxonomy && Array.isArray(data.taxonomy)) {
      data.taxonomy.forEach(t => {
        ((t && t.mitre_tags) || []).forEach(m => {
          if (m && !mitreTags.some(existing => existing.technique_id === m.technique_id)) {
            mitreTags.push(m);
          }
        });
      });
    }

    // Collect artifacts
    const artifacts = data.artifacts || {};
    const emailChips = ((artifacts.emails || []).map(e => e && e.value)).filter(Boolean);
    const paymentChips = ((artifacts.payment_identifiers || []).map(p => p && p.value)).filter(Boolean);
    const phoneChips = ((artifacts.phones || []).map(ph => ph && ph.value)).filter(Boolean);

    drawer.innerHTML = `
      <div class="jobshield-header">
        <div class="jobshield-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2.5">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>JobShield Threat Report</span>
        </div>
        <button class="jobshield-close-btn" id="jobshield-close-drawer">✕</button>
      </div>

      <div class="jobshield-body">
        <div class="jobshield-score-card">
          <div>
            <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700;">Risk Severity Index</div>
            <div class="jobshield-risk-number ${colorClass}">${riskScore}<span style="font-size: 16px; color: #64748b;">/100</span></div>
          </div>
          <div class="jobshield-badge ${badgeClass}">${riskLevel} RISK</div>
        </div>

        <div class="jobshield-action-box">
          <strong>${data.action || "ASSESSMENT"}:</strong> ${data.recommendation || "Review details carefully."}
        </div>

        ${findings.length > 0 ? `
          <div>
            <div class="jobshield-section-title">Key Security Findings</div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              ${findings.slice(0, 3).map(f => `
                <div style="font-size: 12px; padding: 6px 10px; background: rgba(255,255,255,0.03); border-radius: 6px; border-left: 2px solid ${f.severity === 'CRITICAL' ? '#ff0055' : '#00f2fe'};">
                  <strong>[${f.severity}]</strong> ${f.title}
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        ${mitreTags.length > 0 ? `
          <div>
            <div class="jobshield-section-title">MITRE ATT&CK Techniques</div>
            <div class="jobshield-chips-row">
              ${mitreTags.map(m => `
                <a href="${m.url}" target="_blank" class="jobshield-chip jobshield-chip-mitre" style="text-decoration: none;">
                  ${m.technique_id} • ${m.technique_name}
                </a>
              `).join('')}
            </div>
          </div>
        ` : ''}

        ${(emailChips.length > 0 || paymentChips.length > 0 || phoneChips.length > 0) ? `
          <div>
            <div class="jobshield-section-title">Extracted Digital Artifacts</div>
            <div class="jobshield-chips-row">
              ${paymentChips.map(p => `<span class="jobshield-chip" style="color: #ff0055; border-color: rgba(255,0,85,0.3);">💳 ${p}</span>`).join('')}
              ${emailChips.map(e => `<span class="jobshield-chip">✉️ ${e}</span>`).join('')}
              ${phoneChips.map(ph => `<span class="jobshield-chip">📞 ${ph}</span>`).join('')}
            </div>
          </div>
        ` : ''}

        <a href="http://localhost:5173" target="_blank" class="jobshield-btn-dashboard">
          Open Full Threat Dossier in Console →
        </a>
      </div>
    `;

    document.body.appendChild(drawer);
    activeDrawer = drawer;

    drawer.querySelector("#jobshield-close-drawer").addEventListener("click", () => {
      drawer.remove();
      activeDrawer = null;
    });
  }

  // ── Toast Helper ───────────────────────────────────────────
  function showToast(msg) {
    if (activeToast) activeToast.remove();
    const toast = document.createElement("div");
    toast.id = "jobshield-toast";
    toast.innerText = msg;
    document.body.appendChild(toast);
    activeToast = toast;
    setTimeout(() => {
      if (toast) toast.remove();
    }, 4000);
  }

  // ── Runtime Message Listeners ──────────────────────────────
  chrome.runtime.onMessage.addListener((request) => {
    if (request.type === "JOBSHIELD_SCAN_STARTED") {
      showToast("🛡️ Analyzing selected content with JobShield...");
    } else if (request.type === "JOBSHIELD_SCAN_RESULT") {
      renderThreatDrawer(request.payload, { source: "Context Selection", description: request.analyzedText });
    } else if (request.type === "JOBSHIELD_ERROR") {
      showToast(`⚠️ ${request.message}`);
    }
  });

  // Inject FAB after DOM is loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectFloatingActionButton);
  } else {
    injectFloatingActionButton();
  }
})();
