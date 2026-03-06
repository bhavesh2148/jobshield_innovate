# ============================================================
# models/bert_classifier.py — Fine-tune DistilBERT / RoBERTa
# ============================================================

import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from loguru import logger
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from sklearn.metrics import classification_report, roc_auc_score
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    BERT_MODEL_NAME, BERT_MAX_LENGTH, BERT_BATCH_SIZE,
    BERT_EPOCHS, BERT_LEARNING_RATE, BERT_WARMUP_RATIO,
    BERT_MODEL_DIR, PROCESSED_DATA_DIR,
)


# ── Dataset ──────────────────────────────────────────────────
class JobPostingDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            str(self.texts[idx]),
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(self.labels[idx], dtype=torch.long),
        }


# ── Trainer ──────────────────────────────────────────────────
class BERTTrainer:
    def __init__(self, model_name: str = BERT_MODEL_NAME):
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"BERT Trainer | Device: {self.device} | Model: {model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=2
        ).to(self.device)

    def train(self, t_train, tl_train, t_val, tl_val):
        """Fine-tune the model and save the best checkpoint."""
        # Class weights to handle imbalance
        n_real = int((tl_train == 0).sum())
        n_fake = int((tl_train == 1).sum())
        weight_fake = n_real / n_fake
        class_weights = torch.tensor([1.0, weight_fake], dtype=torch.float).to(self.device)
        loss_fn = nn.CrossEntropyLoss(weight=class_weights)

        train_dataset = JobPostingDataset(t_train, tl_train, self.tokenizer, BERT_MAX_LENGTH)
        val_dataset = JobPostingDataset(t_val, tl_val, self.tokenizer, BERT_MAX_LENGTH)

        train_loader = DataLoader(train_dataset, batch_size=BERT_BATCH_SIZE, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=BERT_BATCH_SIZE, shuffle=False)

        optimizer = AdamW(self.model.parameters(), lr=BERT_LEARNING_RATE, weight_decay=0.01)
        total_steps = len(train_loader) * BERT_EPOCHS
        warmup_steps = int(total_steps * BERT_WARMUP_RATIO)

        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
        )

        best_val_f1 = 0.0
        best_epoch = 0

        for epoch in range(BERT_EPOCHS):
            # ── Train ────────────────────────────────────────
            self.model.train()
            total_loss = 0.0
            for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{BERT_EPOCHS} [train]"):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["label"].to(self.device)

                optimizer.zero_grad()
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                loss = loss_fn(outputs.logits, labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(train_loader)

            # ── Validate ─────────────────────────────────────
            val_preds, val_probs, val_true = self._evaluate(val_loader)
            report = classification_report(val_true, val_preds, output_dict=True)
            val_f1 = report.get("1", {}).get("f1-score", 0.0)
            val_auc = roc_auc_score(val_true, val_probs)

            logger.info(
                f"Epoch {epoch+1} | Loss={avg_loss:.4f} | "
                f"FAKE-F1={val_f1:.4f} | AUC={val_auc:.4f}"
            )

            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_epoch = epoch + 1
                self.save()
                logger.info(f"  ✓ New best model saved (F1={val_f1:.4f})")

        logger.info(f"Training complete. Best epoch: {best_epoch} | F1={best_val_f1:.4f}")

    def _evaluate(self, dataloader):
        """Run inference on a DataLoader; return preds, probs, labels."""
        self.model.eval()
        all_preds, all_probs, all_labels = [], [], []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["label"].numpy()

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=-1)[:, 1].cpu().numpy()
                preds = (probs >= 0.5).astype(int)

                all_preds.extend(preds)
                all_probs.extend(probs)
                all_labels.extend(labels)

        return np.array(all_preds), np.array(all_probs), np.array(all_labels)

    def save(self):
        """Save model and tokenizer to disk."""
        BERT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(BERT_MODEL_DIR)
        self.tokenizer.save_pretrained(BERT_MODEL_DIR)
        logger.info(f"BERT model saved to {BERT_MODEL_DIR}")

    @classmethod
    def load(cls):
        """Load saved BERT model for inference."""
        instance = cls.__new__(cls)
        instance.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        instance.tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_DIR)
        instance.model = AutoModelForSequenceClassification.from_pretrained(
            BERT_MODEL_DIR
        ).to(instance.device)
        instance.model.eval()
        logger.info(f"BERT model loaded from {BERT_MODEL_DIR}")
        return instance

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Return fraud probability for a list of texts."""
        self.model.eval()
        dataset = JobPostingDataset(
            texts,
            [0] * len(texts),   # dummy labels
            self.tokenizer,
            BERT_MAX_LENGTH,
        )
        loader = DataLoader(dataset, batch_size=BERT_BATCH_SIZE, shuffle=False)
        all_probs = []

        with torch.no_grad():
            for batch in loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=-1)[:, 1].cpu().numpy()
                all_probs.extend(probs)

        return np.array(all_probs)


# ── Training Entry Point ─────────────────────────────────────
if __name__ == "__main__":
    t_train = np.load(PROCESSED_DATA_DIR / "t_train.npy", allow_pickle=True)
    t_val = np.load(PROCESSED_DATA_DIR / "t_val.npy", allow_pickle=True)
    tl_train = np.load(PROCESSED_DATA_DIR / "tl_train.npy")
    tl_val = np.load(PROCESSED_DATA_DIR / "tl_val.npy")

    trainer = BERTTrainer()
    trainer.train(t_train, tl_train, t_val, tl_val)
