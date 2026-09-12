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
