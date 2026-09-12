# 🛡️ JobShield — AI-Driven Cyber Defense for Online Recruitment Fraud

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.x-646CFF.svg)](https://vitejs.dev/)
[![Tesseract OCR: 5.4](https://img.shields.io/badge/Tesseract_OCR-5.4-blueviolet.svg)](https://github.com/tesseract-ocr/tesseract)
[![Chrome Extension: Manifest V3](https://img.shields.io/badge/Chrome_Extension-Manifest_V3-success.svg)](https://developer.chrome.com/docs/extensions/mv3/)

> **An enterprise-grade, privacy-first cybersecurity defense platform that detects fraudulent job postings, identity theft, typo-squatted domains, and advance-fee extortion scams in under 3 seconds — 100% locally and completely offline.**

---

## 📖 Overview

**JobShield** addresses the growing crisis of **Online Recruitment Fraud (ORF)**. Threat actors routinely clone legitimate Fortune 500 job postings to harvest candidate Personally Identifiable Information (PII), steal financial assets via advance fees (e.g. equipment deposits, background check fees), or deploy malicious links.

Unlike conventional keyword search tools or opaque black-box machine learning models, JobShield operates as a **deterministic, multi-layered cyber defense pipeline**. It synthesizes:
1. **Low-latency ML Ensemble**: DistilBERT semantics, XGBoost structural risk trees, and Baseline Logistic Regression.
2. **Deterministic Security Rule Engine**: Propositional rules targeting advance fees, corporate identity spoofing, and off-platform redirection.
3. **Forensic Artifact Extractor**: Zero-leakage extraction of crypto wallets, P2P handles (`$CashApp`), phone numbers, emails, and URLs.
4. **Passive Domain & Typo-Squatting Intel**: Offline homoglyph normalization, Damerau-Levenshtein distance, and Shannon entropy DGA detection.
5. **Local Tesseract OCR Ingestion**: 100% offline visual transcription for job flyers, screenshots, and documents with auto-enriching regex metadata parsers.
6. **Chrome Browser Extension (Manifest V3)**: Real-time, in-browser threat scanning for **LinkedIn**, **Indeed**, **Glassdoor**, and **Gmail**.

---

## 🏗️ Architecture & Detection Pipeline

```
                                 [INPUT INGESTION]
               ┌─────────────────────────┬─────────────────────────┐
               │                         │                         │
      Raw Text / Paste         Flyer / Screenshot Image     Chrome Extension
      (Web App Console)         (PNG, JPG, WEBP, TIFF)     (LinkedIn/Indeed/Gmail)
               │                         │                         │
               │                         ▼                         │
               │               Local Tesseract OCR Engine          │
               │              (100% Offline Transcription)         │
               │                         │                         │
               └─────────────────────────┼─────────────────────────┘
                                         ▼
                       [Ingestion Parser & Auto-Enrichment]
                   • Extracts Unicode Ballot Checkboxes (☑ / ☐)
                   • Hydrates Title, Company, Salary, Experience
                   • Prevents Tabular "Default-0" False Positives
                                         │
                                         ▼
                      [Security Artifact Extraction Engine]
                   • Cryptocurrency Wallets (BTC, ETH, Bech32)
                   • P2P Payment Handles ($CashApp, Zelle, PayPal)
                   • Candidate & Recruiter Emails (Free Webmail check)
                   • Telecom-Formatted Domestic & Intl Phone Numbers
                   • URLs, Hostnames, and Hosted Form Endpoints
                                         │
                                         ▼
                     [Deterministic Propositional Rule Engine]
                   • RULE_ADVANCE_FEE_PAYMENT (CRITICAL)
                   • RULE_CORPORATE_IDENTITY_MISMATCH (HIGH)
                   • RULE_OFF_PLATFORM_COMMUNICATION (HIGH/MEDIUM)
                   • RULE_UNOFFICIAL_APPLICATION_FORM (MEDIUM)
                   • RULE_SUSPICIOUS_URGENCY_PAYMENT (HIGH)
                                         │
                                         ▼
                     [Passive Domain & Impersonation Intel]
                   • Homoglyph Normalization (Cyrillic, Greek, Latin)
                   • Damerau-Levenshtein Typo-Squatting Engine
                   • High-Risk TLD Correlation (.xyz, .site, .top)
                   • Shannon Hostname Entropy Metric for DGA Lures
                                         │
                                         ▼
                   [Hybrid Machine Learning & Memory Ensemble]
       ┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
       ▼                         ▼                         ▼                         ▼
   DistilBERT                 XGBoost                 Logistic Reg.             FAISS Index
(Textual Semantics)      (15 Tabular Features)     (Baseline Stabilizer)    (SBERT Vector Memory)
       └─────────────────────────┼─────────────────────────┴─────────────────────────┘
                                 ▼
                    [Evidence & Risk Correlation Engine]
            • Mathematical Non-Linear Risk Floor: Risk = max(ML, Rule)
            • 4-Tier Threat Policy: LOW | MEDIUM | HIGH | CRITICAL
            • Action Directives: SAFE | VERIFY | EXERCISE_CAUTION | DO_NOT_ENGAGE
                                 │
                                 ▼
                     [MITRE ATT&CK Threat Taxonomy]
            • T1657: Financial Theft (Advance-Fee Fraud)
            • T1586.002: Compromised Accounts / Free Webmail Lures
            • T1583.001: Acquire Infrastructure / Typo-Squatting
            • T1566.002: Spearphishing Link / Off-Platform Channel
            • T1598: Phishing for Information / PII Harvesting
```

---

## ✨ Key Capabilities

### 1. 🧠 Multi-Model Detection Ensemble
* **DistilBERT (~50% weight)**: Detects subtle social engineering, artificial urgency, and vague lures in job descriptions.
* **XGBoost (~35% weight)**: Analyzes 15 tabular features (e.g. missing salary, telecommuting flags, profile completeness).
* **Logistic Regression (~15% weight)**: Baseline regularizer preventing edge-case overconfidence.
* **SBERT + FAISS Vector Memory**: Embeds confirmed scam templates using `all-MiniLM-L6-v2`. If cosine similarity to known scam clusters exceeds `0.85`, risk is elevated automatically.

### 2. 🛡️ Propositional Cybersecurity Rules & Non-Linear Escalation
* Statistical models can be fooled when threat actors copy legitimate job descriptions word-for-word.
* JobShield applies deterministic cybersecurity overrides: if a direct crypto wallet, CashApp fee, or unmonitored Telegram interview is detected, the threat posture escalates immediately to **`CRITICAL` (`DO_NOT_ENGAGE`)**, regardless of benign text probability.

### 3. 🌐 Passive Local Domain & Brand Impersonation Intel
* **100% Local & Offline**: Operates without live external DNS or WHOIS queries, preventing candidate browsing leaks.
* **Typo-Squatting**: Flags domains with Damerau-Levenshtein edit distance $\le 2$ targeting 100+ curated enterprise brands (`g00gle.com`, `inf0sys.com`, `micros0ft.com`).
* **Homoglyph Detection**: Detects lookalike Unicode characters (e.g. Cyrillic `а` `\u0430`, Latin dotless `ı` `\u0131`).
* **Shannon Entropy**: Calculates hostname character distribution entropy ($H \ge 3.2$ on 8+ character stems with digits) to flag Algorithmically Generated Domains (DGAs).

### 4. 📄 100% Local OCR Ingestion & Real-Time Parser
* Integrated with **Tesseract OCR `v5.4`** for offline image-to-text extraction from job flyers, screenshots, and offer letters.
* Intelligent ingestion parser extracts checkboxes (`☑ Yes`, `☐ No`), salary ranges, and company metadata to hydrate the tabular feature vector, eliminating the historical "default-0" false positive penalty.

### 5. 🧩 Google Chrome Browser Extension (Manifest V3)
* Scrapes active job postings on **LinkedIn**, **Indeed**, **Glassdoor**, and **Gmail**.
* Right-click context-menu: **"🛡️ Scan Selection with JobShield"**.
* In-page floating action button (**🛡️ Scan with JobShield**) and an editorial glassmorphic sliding threat report drawer with MITRE ATT&CK technique tags.
* Standalone popup console with live backend health monitoring.

### 6. 🔍 Explainable AI (XAI) & Adaptive Defense
* **SHAP (SHapley Additive exPlanations)**: Mathematically quantifies the positive or negative risk attribution of every tabular feature.
* **Interactive Phrase Highlighting**: Visually highlights high-pressure phrases and suspicious entities.
* **Concept Drift Detection**: Real-time sliding window distribution monitoring (`api/drift.py`) tracks emerging threat patterns.
* **Human-in-the-Loop Feedback**: Candidate feedback collection with constant-time authenticated admin retraining triggers.

---

## 📋 System Requirements

* **Operating System**: Windows 10/11, macOS (12+), or Ubuntu (20.04+)
* **Python**: `3.10`, `3.11`, or `3.12`
* **Node.js**: `18.x` or `20.x` (with `npm`)
* **Browser**: Google Chrome / Brave / Edge (for Chrome Extension)
* **OCR Binary (Optional but Recommended)**: Tesseract OCR `v5.0+`

---

## 🚀 Quickstart Installation Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/bhavesh2148/jobshield_innovate.git
cd jobshield_innovate
```

---

### Step 2: Set Up Python Backend

1. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   ```bash
   # Copy sample configuration
   cp .env.example .env
   ```
   *(By default, `.env` runs out of the box with safe local defaults and a secure random admin token).*

4. **Launch the FastAPI Server**:
   ```bash
   uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   * **API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   * **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) (`status: ok, models_loaded: true`)

---

### Step 3: Set Up React Frontend

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   * **Web Dashboard**: [http://localhost:5173/](http://localhost:5173/)

---

### Step 4: Install Tesseract OCR (For Visual / Screenshot Scanning)

* **Windows**:
  Download and run the installer from the [UB-Mannheim Tesseract Project](https://github.com/UB-Mannheim/tesseract/wiki).  
  *JobShield automatically discovers Tesseract at `C:\Program Files\Tesseract-OCR` or `~\AppData\Local\Programs\Tesseract-OCR`.*
* **macOS**:
  ```bash
  brew install tesseract
  ```
* **Ubuntu / Debian**:
  ```bash
  sudo apt update && sudo apt install -y tesseract-ocr
  ```

---

### Step 5: Install the Google Chrome Extension

1. Open Google Chrome and visit:
   ```text
   chrome://extensions
   ```
2. Enable the **Developer mode** toggle in the top-right corner.
3. Click the **Load unpacked** button in the top-left corner.
4. Select the `extension/` folder in your cloned repository:
   ```text
   path/to/jobshield_innovate/extension
   ```
5. Pin the **JobShield 🛡️** icon to your browser toolbar!

---

## 🧪 Verification & Automated Testing

Run the automated test suite to ensure all security modules, artifact extractors, and integration phases pass:

```bash
# 1. Run all unit tests across cybersecurity engines (34 tests)
pytest tests/test_domain_intel.py tests/test_rule_engine.py tests/test_artifact_extractor.py tests/test_correlation_engine.py tests/test_job_parser.py

# 2. Run the full multi-phase integration test suite (31 checks)
python tests/test_integration_all_phases.py
```

### Expected Output:
```text
============================== 34 passed in 0.82s ==============================
INTEGRATION TEST COMPLETE: 31/31 checks passed
ALL PHASES (0-6) VERIFIED AND WORKING IN SYNC
```

---

## 🔒 Security & Privacy Commitments

| Guarantee | Policy |
| :--- | :--- |
| **Data Sovereignty** | 100% Local execution. Zero candidate data or scraped job postings are ever transmitted to third-party cloud servers. |
| **API Boundary Hardening** | Pydantic v2 input sanitization, strict string bounds, and constant-time secret comparison (`secrets.compare_digest`). |
| **Passive Domain Threat Intel** | Zero active DNS lookups or external WHOIS polling. All typo-squatting and homoglyph analyses run entirely in local memory. |
| **OCR Privacy** | Tesseract OCR runs strictly as a local subprocess. No image bytes leave the device. |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
