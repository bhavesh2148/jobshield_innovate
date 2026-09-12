# JobShield — Phase 1: Investigation & Threat Dossier UI Shell

## Executive Summary

Phase 1 aligns JobShield's user interface with a disciplined cybersecurity investigation model. Prior to this phase, the application exposed a tabular 14-field form that modeled a dataset row rather than an unsolicited recruitment threat, and presented results as a binary "REAL/FAKE" coin flip with raw statistical gradient numbers.

Phase 1 refactors this into:
1. An **unstructured threat ingestion console** accepting free-form job descriptions, emails, or messages, plus a screenshot attachment dropzone.
2. A formal **Investigation Dossier** presenting JobShield's 4-tier risk stratification model (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), actionable guidance (`RecommendationAction`), and model-derived indicators without exposing raw SHAP mathematical values.
3. Cleaned, focused navigation (`Home`, `Investigate`, `Dossier`, `Admin`).

Zero changes were made to backend APIs, schemas, or models, preserving local-first execution.

---

## Technical & Conceptual Breakdown

### 1. Ingestion Paradigm Shift: Dataset Form → Unstructured Threat Ingestion
* **Previous State**: Required the user to dissect content into 14 distinct attributes: `title`, `company`, `description`, `requirements`, `benefits`, `telecommuting`, `has_company_logo`, `has_questions`, etc.
* **Problem**: In real-world recruitment fraud, targets receive unstructured text — an unsolicited LinkedIn message, an email, or an unfamiliar job board URL snippet. Forcing users to extract attributes creates heavy cognitive load.
* **Solution**: The primary input is now a single prominent investigation textarea. Text entered is sent via the `description` parameter, ensuring backward compatibility with the existing feature extraction pipeline.
* **Optional Context Drawer**: `Job Title` and `Company / Organization` remain available in a subtle collapsible drawer for cases where the analyst knows the target entity.
* **Screenshot Artifact Ingestion**: A drag-and-drop file attachment zone is visually present for screenshots (supporting PNG, JPG, and WEBP). It handles local file attachment state gracefully, laying the UI foundation for the Phase 6 OCR pipeline without misleading marketing jargon.

### 2. Output Paradigm Shift: Binary Verdict → Investigation Dossier
* **Previous State**: Banners reading `"FRAUDULENT THREAT DETECTED"` or `"VERIFIED LOW RISK"` accompanied by raw numbers like `Impact: +0.342 · Elevates Threat`.
* **Problem**: Binary classification obscures the nuance of recruitment threat operations (which range from benign listings with missing metadata to high-urgency credential theft and financial scams). Presenting raw SHAP values confuses analysts and conflates statistical model feature attribution with verified security evidence.
* **Solution**:
  - **4-Tier Risk Stratification**: Dynamically displays `CRITICAL RISK POSTURE`, `HIGH RISK POSTURE`, `ELEVATED RISK POSTURE`, or `LOW RISK POSTURE`, reflecting JobShield's risk model.
  - **Actionable Operational Guidance**: Highlights the contract action (`DO_NOT_ENGAGE`, `MANUAL_VERIFICATION_REQUIRED`, `PROCEED_WITH_CAUTION`, `SAFE_TO_PROCEED`) alongside clear recommendation text.
  - **Model-Derived Contributing Indicators**: SHAP feature attributions are clearly demarcated as statistical model factors rather than verified forensic evidence. Raw decimal numbers are omitted in favor of qualitative directional badges (*Elevates Risk* / *Reduces Risk*).
  - **Cataloged Scam Proximity & Red Flags**: Retains FAISS vector similarity to cataloged threat signatures and interactive phrase highlighting.

### 3. Navigation Clean-up
* Removed dead menu links (`Campaigns` and `About`), which previously looped to the admin retraining page.
* Streamlined navigation:
  - `Home`: Marketing overview & threat vectors.
  - `Investigate`: Threat ingestion console.
  - `Dossier`: Active investigation dossier (enabled once an evaluation has been performed).
  - `Admin`: Drift metrics and retraining controls.

---

## Files Modified

| File | Type of Change | Key Details |
|---|---|---|
| `frontend/HomePage.jsx` | Refactor | Implemented single unstructured textarea, screenshot upload area, collapsible optional metadata drawer (`title`, `company`), and streamlined status indicators. |
| `frontend/ResultsPage.jsx` | Refactor | Replaced binary verdict with 4-tier risk posture, operational recommendation badge, qualitative model-derived indicators (no raw SHAP numbers), and dossier styling. |
| `frontend/App.jsx` | Modification | Removed dead `Campaigns` and `About` links; renamed `Threats` to `Dossier`. |

---

## Files Strictly Untouched

* `frontend/LandingPage.jsx`: Left intact.
* `frontend/AdminPage.jsx`: Preserved.
* `api/*`: Untouched. Zero API contract changes.
* `ensemble/*`, `explainability/*`, `drift_detection/*`: Untouched.
* Dependencies: Zero new npm packages installed.

---

## Verification & Testing Procedure

1. **Verify Ingestion**:
   - Navigate to `http://localhost:5173/` and click "Investigate".
   - Confirm that the primary view displays the single large text area and screenshot dropzone.
   - Click "Add Optional Context" to confirm the drawer expands smoothly to expose Title and Company.
2. **Verify Submission & Compatibility**:
   - Paste a sample job posting or recruiter message into the main box.
   - Click "Run Threat Assessment →".
   - Confirm that the request executes against `http://localhost:8000/predict` and transitions smoothly to the Dossier view.
3. **Verify Dossier Output**:
   - Confirm the banner displays the appropriate 4-tier posture (`CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`) and threat score.
   - Confirm that `Operational Recommendation` displays the action badge (e.g. `DO NOT ENGAGE` or `MANUAL VERIFICATION REQUIRED`).
   - Confirm that `Model-Derived Contributing Indicators` display plain English indicators with "Elevates Risk" / "Reduces Risk" without raw decimal numbers.
4. **Verify Navigation**:
   - Confirm that dead links are gone and the "Dossier" tab is accessible.
