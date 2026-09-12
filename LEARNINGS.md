# JobShield — Engineering Learnings & Architectural Knowledge Base

This document records the foundational lessons learned, edge-case postmortems, and key design trade-offs discovered while developing and testing JobShield in real-world conditions.

---

## 1. The Real-World Recruitment Threat Landscape

### Lesson: Fraud Is Not Just Text, It Is A Workflow
* **Traditional Approach**: Treating fraud detection as an NLP sentiment classification task.
* **Why It Fails**: Scammers copy real job descriptions word-for-word from Fortune 500 portals (Google, Infosys, Amazon). The job description itself is frequently 100% legitimate text.
* **The Actual Attack Vector**: The fraud lives in the **workflow modifications**:
  1. Off-platform redirect (e.g., Telegram, Signal, WhatsApp).
  2. Consumer email domains pretending to be corporate recruiting (e.g., `careers-google@gmail.com`).
  3. Pre-employment financial solicitations (e.g., equipment purchase, background check deposits, crypto wallets).
  4. Credential harvesting forms (e.g., Google Forms asking for SSNs or banking details).
* **Takeaway**: Statistical ML must be paired with **deterministic propositional cybersecurity rules** and **hierarchical artifact extraction** to detect the true attack surface.

---

## 2. Ingestion Inconsistency & The "Default-0" Tabular Bias (Infosys Postmortem)

### The Phenomenon
When testing a verified, authentic enterprise posting for **Infosys Limited** (Full Stack Developer, Chennai):
```text
Field Value Job Title Full Stack Developer Company Name Infosys Limited Salary Range $70,000–$95,000/year 
Employment Type Full-time Experience Required Associate level Has Company Logo ☑ Yes 
Has Screening Questions ☑ Yes Remote / Telecommute ☐ No Job Description: Infosys Limited is hiring...
```
JobShield flagged it as **78.3% FAKE / HIGH RISK POSTURE** (Risk Score 78/100).

### The Root Cause
1. **Model Architecture**:
   * **DistilBERT**: Evaluates textual semantics.
   * **XGBoost & Logistic Regression**: Evaluates 15 tabular features from the EMSCAD benchmark dataset.
2. **Dataset Bias**:
   * In historical training data, >90% of fraudulent listings omit company profiles (`has_company_profile == 0`), company logos (`has_logo == 0`), and screening questions (`has_questions == 0`).
   * Consequently, XGBoost learned to assign massive risk penalties (+1.73 SHAP for missing company profile, +0.37 SHAP for missing logo) whenever these fields are `0`.
3. **Ingestion Gap**:
   * In a streamlined single-textarea console, the user pastes the entire job specification (including headers like `Company Name: Infosys Limited`, `Has Company Logo: Yes`) into the description box.
   * The client submitted all other schema fields as default/empty (`has_company_logo = 0`, `company_profile = ""`).
   * The tabular model interpreted this as a suspicious listing with no corporate credentials, overwhelming the benign text score.

### Empirical Validation
| Submission Method | Prediction | Risk Score | Confidence | Primary SHAP Attribution |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Description Paste** | **FAKE** | **83 / 100** | **83.4%** | `Missing company profile (+1.73)`<br>`No company logo (+0.37)` |
| **Structured Schema** | **REAL** | **4 / 100** | **96.2% REAL** | `Experience req specified (-1.49)`<br>`Industry alignment (-0.95)`<br>`Company profile present (-0.76)` |

### Architectural Resolution
* **Intelligent Ingestion Parser (`utils/job_parser.py`)**: Automatically detects inline key-value pairs (`Company Name:`, `Has Company Logo: Yes`, `Salary:`, etc.) from raw text pastes to hydrate the structured feature vector automatically.
* **Explicit Frontend Ingestion Controls (`HomePage.jsx`)**: Provides toggles for `Company Logo Present` and `Screening Questions Present` so users can explicitly confirm them, alongside real-time detected metadata chips.

---

## 3. The Offline & Privacy-First Execution Imperative

### Lesson: Candidate Data Cannot Leave The Local Machine
* Candidates analyzing suspicious correspondence frequently paste sensitive personal details (names, personal email addresses, phone numbers, compensation histories, offer letters).
* Transmitting this content to external APIs (OpenAI, Anthropic, cloud OCR) creates an immediate data leak risk.
* **Architecture Rules**:
  1. All models (DistilBERT, XGBoost, FAISS) run 100% locally via PyTorch and ONNX/Scikit-learn.
  2. OCR runs 100% offline via local Tesseract.
  3. Zero external outbound telemetry.

---

## 4. Multi-Signal Evidence Correlation: The 2-Tier Rule Escalation

### Lesson: Rules Override Statistical Probabilities Under Critical Danger
* When an advance-fee crypto wallet or a consumer email impersonating a Fortune 500 company is detected, **statistical NLP uncertainty is irrelevant**.
* Even if DistilBERT rates a text as 90% benign (because the scammer copied legitimate text), the presence of a known fraudulent wallet or off-platform redirection must escalate the posture to **CRITICAL RISK (`DO_NOT_ENGAGE`)**.
* The **Phase 4 Correlation Engine** codifies this non-linear override:
  $$\text{Risk} = \max(\text{ML\_Probability}, \text{Deterministic\_Severity\_Floor})$$

---

## 5. Local OCR Architecture & The Layered Ingestion Model

### The Common Misconception: "OCR Understands Scams"
A frequent assumption when integrating OCR is expecting the optical recognition engine itself to output structured entities (identifying "the recruiter's email", "the salary", or classifying whether the image is a scam).
* **The Reality**: Tesseract OCR is strictly a **low-level 2D raster-to-text transcription engine**. It ingests a pixel array and outputs a UTF-8 character string. It has zero semantic awareness of cybersecurity, recruitment fraud, or entity schemas.

### The 5-Stage Ingestion-to-Verdict Pipeline
JobShield decomposes visual document inspection into a deterministic 5-stage funnel:

```
┌────────────────────────────────────────────────────────┐
│  Stage 1: Local Ingestion (Tesseract OCR Engine)       │
│  Transforms screenshot pixels → Raw Plaintext String   │
└──────────────────────────┬─────────────────────────────┘
                           │ Raw Text
                           ▼
┌────────────────────────────────────────────────────────┐
│  Stage 2: Structural Ingestion Parser                  │
│  Extracts checkboxes (☑/☐), Title, Company, Salary     │
└──────────────────────────┬─────────────────────────────┘
                           │ Hydrated Text + Metadata
                           ▼
┌────────────────────────────────────────────────────────┐
│  Stage 3: Security Artifact Extractor                  │
│  Extracts observable indicators: Emails, URLs, Phones, │
│  Crypto wallets (BTC/ETH), P2P handles ($CashApp, etc) │
└──────────────────────────┬─────────────────────────────┘
                           │ Artifact Report
                           ▼
┌────────────────────────────────────────────────────────┐
│  Stage 4: Security Rule & Correlation Engine           │
│  Correlates signals: Advance-fee fraud, brand mismatch,│
│  maps to MITRE ATT&CK techniques (T1657, T1566.002)    │
└──────────────────────────┬─────────────────────────────┘
                           │ Findings & Context
                           ▼
┌────────────────────────────────────────────────────────┐
│  Stage 5: Hybrid ML Ensemble (DeBERTa + SBERT + Tab)   │
│  Produces final Risk Score (0-100), Level & Action     │
└────────────────────────────────────────────────────────┘
```

### Windows Privilege Isolation & Administrative MSI Extraction
* **The Trap**: Standard Windows installers (`.exe` built with NSIS) embed `requestedExecutionLevel level="requireAdministrator"`. Executing them in automated or non-interactive environments triggers `OSError: [WinError 740] The requested operation requires elevation` or halts on hidden UAC prompts.
* **The Solution**:
  1. Use administrative network extraction: `msiexec /a 7z.msi /qn TARGETDIR=...` to extract portable extraction binaries without requiring root or admin privileges.
  2. Use the portable extractor to unpack the Tesseract archive directly into the user-local profile: `~\AppData\Local\Programs\Tesseract-OCR`.
  3. Pre-configure `ocr/engine.py` and `pytesseract` to discover the user-local binary path automatically.
  4. This guarantees 100% offline, zero-admin installation and execution.

---

## 6. Cross-Platform Console Encoding & Non-ASCII Serialization

### The Windows `cp1252` Encoding Hazard
* **The Bug**: On Windows terminals, default standard I/O operates in legacy code pages (e.g., `cp1252`). When Python tests or CLI scripts print Unicode symbols (such as arrows `→`, ballot checkboxes `☑`, or mathematical notations), Python throws unhandled `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'`.
* **The Fix**: Proactively reconfigure runtime standard streams at test and application entrypoints:
  ```python
  import sys
  if hasattr(sys.stdout, "reconfigure"):
      sys.stdout.reconfigure(encoding="utf-8")
  if hasattr(sys.stderr, "reconfigure"):
      sys.stderr.reconfigure(encoding="utf-8")
  ```

---

## 7. Threat Taxonomy & MITRE ATT&CK Formalization

### Moving Beyond Generic "Scam / Not Scam" Labels
Generic classifications fail enterprise security analysts and confuse candidates. JobShield maps detected evidence directly to formal cyber threat tactics and techniques under the MITRE ATT&CK framework:
1. **Advance-Fee Recruitment Fraud (`T1657` - Financial Theft)**:
   * Trigger: Solicitation of deposits, background check fees, equipment fees, or payment transfers via CashApp, Zelle, Bitcoin, or Ethereum.
2. **Corporate Brand & Identity Impersonation (`T1586.002` - Compromised Accounts / External Webmail)**:
   * Trigger: High-prestige corporate brand claimed in job title/metadata while recruiter contact utilizes consumer webmail (`@gmail.com`, `@yahoo.com`, `@proton.me`).
3. **Off-Platform Communication Redirection (`T1566.002` - Spearphishing Link / `T1598` - Phishing for Information)**:
   * Trigger: Forcing applicants away from monitored corporate portals to private messaging channels (Telegram, Signal, WhatsApp) to evade enterprise logging and compliance.

---

## 8. Adaptive Defense: Drift Detection & Safe Pseudo-Labeling

### Continuous Self-Training Guardrails
* **The Problem**: Threat actor vocabulary shifts rapidly (new cryptocurrency tokens, novel phrasing for remote work lures).
* **The Safeguard**: To prevent model degradation or feedback poisoning:
  1. Samples are only pseudo-labeled if model confidence exceeds **95%**.
  2. Samples with active deterministic security violations (`CRITICAL` or `HIGH` rule findings) are never admitted as benign pseudo-labels.
  3. Concept drift is continuously tracked using a sliding-window distribution monitor (`api/drift.py`).
  4. Retraining endpoints are protected with constant-time token comparison (`secrets.compare_digest`) to prevent timing side-channel attacks.

---

## 9. Comprehensive Project Status & Remaining Roadmap Assessment

### What Is Fully Complete (Phases 0 through 6)
* **Phase 0: Boundary Hardening & Security Foundations** (Pydantic validation, 4-tier threat policy, constant-time secrets).
* **Phase 1: Dual-Interface Web Experience** (FastAPI backend + Vite React editorial dark-mode frontend with threat dossiers and SHAP visualization).
* **Phase 2: Security Artifact Extraction** (Zero-leakage extraction of emails, URLs, domains, phones, crypto addresses, and P2P handles).
* **Phase 3: Deterministic Rule Engine** (Propositional logic for advance-fee fraud, brand mismatch, off-platform redirection).
* **Phase 4: Evidence & Risk Correlation Engine** (Non-linear risk escalation and unified finding synthesizers).
* **Phase 5: Threat Taxonomy & MITRE ATT&CK Mapping** (Automated classification of threat profiles and MITRE tags).
* **Phase 6: Local OCR Ingestion & Real-Time Parsing** (Offline Tesseract OCR + regex key-value/checkbox auto-enrichment).

### What Remains on the Master Roadmap
Beyond the **Chrome Browser Extension**, there were two additional components previously designed in the system blueprint:

1. **Phase 7: Passive Local Domain & Impersonation Analysis (`security/domain_intel.py`)**:
   * Offline Levenshtein & homoglyph distance detection against curated Fortune 500 domains (e.g., detecting `g00gle.com`, `strıpe.com` with dotless `ı`, `infosys-careers.site`).
   * Local Shannon entropy calculation on hostnames to flag algorithmically generated disposable domains (DGAs) without making live DNS/whois lookups (preserving 100% offline privacy).
2. **Phase 8: Browser Extension (Chrome Ingestion Interface) (`extension/`)**:
   * Manifest V3 extension with context-menu ("Scan Selection with JobShield") and auto-parser for LinkedIn/Indeed/Gmail.
   * Directly queries the local backend (`http://localhost:8000/predict`) and renders an in-page threat badge.
3. **Phase 9: Docker Containerization (`Dockerfile`, `docker-compose.yml`)**:
   * Single command (`docker compose up`) that packages Python, PyTorch, FAISS, Tesseract OCR binary, and Vite frontend into an isolated, reproducible container for demonstration or deployment.
4. **Phase 10: Local Mailbox / Gmail Ingestion (Stretch)**:
   * Direct `.eml` / local mailbox file ingestion utility.
