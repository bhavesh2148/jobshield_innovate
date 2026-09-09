# ️ JobShield: AI-Driven CyberSecurity for Online Recruitment Fraud

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

**A CyberSecurity and Threat Defense system that detects fraudulent job postings and social engineering scams instantly — 100% local, zero cloud dependency.**

---

## 📖 Overview

**JobShield** is an AI-powered **CyberSecurity application** designed to combat Online Recruitment Fraud (ORF). Fraudulent job postings are a growing vector for phishing, identity theft (stealing Aadhaar, PAN, and bank details), and financial extortion. 

Unlike traditional keyword filters or black-box ML models, JobShield operates as an intelligent threat detection pipeline. It runs a three-model ensemble simultaneously to classify job postings in under 3 seconds, delivering a REAL/FAKE verdict, a confidence score, plain-language threat explanations, and a similarity check against known scam signatures — all running locally on a standard CPU.

---

##  The Cybersecurity Problem
- **Social Engineering & Phishing:** Scammers exploit open job portals to harvest sensitive PII (Personally Identifiable Information) and extort "registration fees."
- **Evasion Tactics:** Fraudsters constantly rephrase scam templates to bypass static keyword filters.
- **Black-Box Models:** Existing ML tools give a verdict without explaining *why*, making it impossible for HR or users to verify the threat.
- **Data Privacy Risks:** Cloud-based moderation tools require sending sensitive job data to external servers, violating data sovereignty.

**JobShield addresses all these gaps in one integrated, privacy-first security pipeline.**

---

## ✨ Key Security & AI Features

### 🧠 3-Model Threat Detection Ensemble
Combines the strengths of three distinct models using Nelder-Mead auto-tuned soft voting:
- **DistilBERT (~50% weight):** Analyzes linguistic patterns, vague urgency, and social engineering red flags in the text.
- **XGBoost 500 trees (~35% weight):** Detects structural anomalies (free email domains, missing salary, spam keyword density).
- **Logistic Regression (~15% weight):** Acts as a stabilizing baseline to prevent overconfident false positives.

### 🔍 Threat Intelligence & Scam Memory (FAISS)
- **Vectorized Scam Database:** Stores embeddings of confirmed fake jobs using SBERT (all-MiniLM-L6-v2).
- **Rephrased Scam Detection:** If a new posting has a cosine similarity > 0.85 to a known scam in the FAISS index, the threat score is automatically boosted — catching variants of scams the classifier hasn't seen before.

### 🛡️ Full Explainability (XAI) for Auditing
- **SHAP Values:** Mathematically traces every prediction back to specific features.
- **Phrase Highlighting:** Suspicious words and social engineering triggers are highlighted directly in the job text.
- **Plain English Audit Trail:** Users get clear, verifiable reasons for the verdict, building trust and enabling manual review.

### 📊 Adaptive Threat Monitoring (Drift Detection)
- **ADWIN (River Library):** Monitors the stream of prediction probabilities in real-time.
- **Auto-Alerts:** Triggers a retraining flag in the Admin Dashboard if fraud patterns shift significantly, ensuring the system doesn't silently degrade as scammers evolve their tactics.

### 🔒 Zero-Trust & Privacy-First Architecture
- **100% Local Execution:** Zero data leaves the machine. No external API keys, no cloud subscriptions, and no data exposure. Ideal for strict enterprise and government compliance.

---

## 🚀 Performance Metrics

| Metric | Score |
| :--- | :--- |
| **AUC-ROC** | **0.9827** |
| **FAKE Class F1** | **0.8485** |
| **Inference Time** | **< 3 seconds** (Standard CPU) |
| **Dataset** | Kaggle EMSCAD (17,880 records, ~5% fraud rate) |

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Machine Learning & NLP** | DistilBERT (HuggingFace), XGBoost, Logistic Regression, SHAP, SMOTENC |
| **Threat Intelligence** | Sentence-BERT, FAISS (Vector Search), ADWIN (Drift Detection) |
| **Backend API** | FastAPI, Uvicorn, Python 3.12, PyTorch, SciPy (Nelder-Mead) |
| **Frontend UI** | React 18, Vite, Framer Motion |
| **Dataset** | Kaggle EMSCAD Fake Job Postings |

---

## 🏗️ System Architecture

The pipeline processes every job posting through four sequential security layers:
1. **Feature Extraction:** Splits input into a Text Path (DistilBERT, 256 tokens) and a Structured Path (11 metadata features scaled via StandardScaler).
2. **Ensemble Prediction:** Merges probabilities via weighted soft voting.
3. **Memory Check:** SBERT encodes the text and queries the FAISS index for known scam variants.
4. **Output & Monitoring:** Packages the JSON response with SHAP explanations and feeds the probability stream to the ADWIN drift detector.

---

## 📦 Installation & Setup

### Prerequisites
- **Python:** 3.10 - 3.12
- **Node.js:** v16 or higher (includes npm)
- **Hardware:** 8GB RAM minimum (16GB recommended for smooth ML inference)

### 1. Backend Setup (FastAPI)
```bash
# Clone the repository
git clone https://github.com/introxxzz/jobshield.git
cd jobshield

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Navigate to the backend folder and start the server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

The backend API will now be running at http://localhost:8000. Keep this terminal open.

2. Frontend Setup (React + Vite)

# Open a NEW terminal window (keep the backend running in the first one)
# Navigate to the frontend directory from the root folder
cd jobshield/frontend

# Install Node.js dependencies
npm install

# Start the Vite development server
npm run dev

The frontend application will be running at http://localhost:5173 (or the port specified in your terminal output).

3. Running the Application

1. Ensure both the Backend (port 8000) and Frontend (port 5173) servers are running concurrently.
2. Open your web browser and navigate to http://localhost:5173.
3. Navigate to the Analyze Dashboard, paste a suspicious job posting, and click to get an instant threat assessment.

Defending job seekers from cyber fraud and social engineering, one posting at a time. 🛡️
