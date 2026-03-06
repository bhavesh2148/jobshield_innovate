# 🔍 Fake Job Detection System

Production-ready AI system to detect fraudulent job postings using an ensemble of BERT, XGBoost, and Logistic Regression — fully local, no external APIs.

---

## 🏗️ Architecture

```
Input Job Posting
       │
       ▼
┌─────────────────────────────────────────────┐
│              Data Pipeline                  │
│  Text Cleaning → Feature Engineering       │
└─────────────┬───────────────┬──────────────┘
              │               │
              ▼               ▼
     ┌────────────┐   ┌───────────────┐
     │ BERT/      │   │  Structured   │
     │ RoBERTa    │   │  Features     │
     │ Embeddings │   │  (XGB + LR)   │
     └─────┬──────┘   └──────┬────────┘
           │                 │
           └────────┬────────┘
                    ▼
          ┌──────────────────┐
          │  Weighted Soft   │
          │  Voting Ensemble │
          └────────┬─────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   SHAP/LIME    FAISS       Drift
   Explain    Similarity   Detect
        │          │          │
        └──────────┴──────────┘
                   │
                   ▼
           FastAPI Backend
                   │
                   ▼
           React Frontend
```

---

## 📁 Folder Structure

```
fake-job-detector/
├── data/                    # Dataset storage & preprocessing
│   ├── raw/                 # Raw Kaggle dataset
│   ├── processed/           # Cleaned & encoded data
│   └── pseudo_labeled/      # Self-training additions
├── models/                  # Saved model files
│   ├── bert/                # Fine-tuned BERT
│   ├── xgboost/             # XGBoost model
│   └── logistic/            # Logistic Regression
├── ensemble/                # Ensemble logic & weight tuning
├── explainability/          # SHAP + phrase highlighting
├── memory/                  # FAISS vector store (SBERT)
├── self_training/           # Pseudo-label & retrain logic
├── drift_detection/         # ADWIN drift detector
├── api/                     # FastAPI backend
├── frontend/                # React UI
├── utils/                   # Shared utilities
├── scripts/                 # Training & setup scripts
└── config/                  # Configuration files
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Dataset
```bash
# Download from Kaggle: fake_job_postings.csv
# Place in: data/raw/fake_job_postings.csv
python scripts/download_data.py
```

### 3. Preprocess & Train
```bash
python scripts/preprocess.py
python scripts/train_bert.py
python scripts/train_xgb_lr.py
python scripts/tune_ensemble_weights.py
python scripts/build_faiss_index.py
```

### 4. Start Backend
```bash
uvicorn api.main:app --reload --port 8000
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 Model Performance Targets

| Metric        | Target  |
|---------------|---------|
| Accuracy      | > 97%   |
| Recall (FAKE) | > 95%   |
| Precision     | > 94%   |
| F1 Score      | > 96%   |

---

## 🔌 API Endpoints

| Endpoint        | Method | Description                |
|-----------------|--------|----------------------------|
| `/predict`      | POST   | Full prediction + explain  |
| `/explain`      | POST   | Detailed SHAP explanation  |
| `/feedback`     | POST   | Submit correction          |
| `/retrain`      | POST   | Trigger retraining         |
| `/admin/stats`  | GET    | Admin dashboard data       |
| `/health`       | GET    | Health check               |

---

## 📦 Key Dependencies

- `transformers` — BERT/RoBERTa
- `sentence-transformers` — SBERT embeddings
- `xgboost` — Gradient boosting
- `faiss-cpu` — Vector similarity
- `shap` — Explainability
- `imbalanced-learn` — SMOTENC
- `river` — ADWIN drift detection
- `fastapi` — Backend API
- `react` + `vite` — Frontend
