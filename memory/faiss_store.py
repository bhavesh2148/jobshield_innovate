# ============================================================
# memory/faiss_store.py — SBERT + FAISS vector similarity
# ============================================================

import pickle
import faiss
import numpy as np
from pathlib import Path
from loguru import logger
from sentence_transformers import SentenceTransformer

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    SBERT_MODEL_NAME, FAISS_INDEX_PATH, FAISS_METADATA_PATH,
    SIMILARITY_THRESHOLD, PROCESSED_DATA_DIR,
)


class FAISSMemoryStore:
    """
    Stores SBERT embeddings of known fake job postings in a
    FAISS index for fast cosine similarity lookup.

    At inference time, if a new job is highly similar to a
    known fake (cosine similarity > threshold), the fraud
    probability is boosted.
    """

    def __init__(self):
        logger.info(f"Loading SBERT model: {SBERT_MODEL_NAME}")
        self.encoder = SentenceTransformer(SBERT_MODEL_NAME)
        self.index = None
        self.metadata = []  # list of dicts per stored entry
        self._try_load()

    # ── Persistence ───────────────────────────────────────────
    def _try_load(self):
        if FAISS_INDEX_PATH.exists() and FAISS_METADATA_PATH.exists():
            self.index = faiss.read_index(str(FAISS_INDEX_PATH))
            with open(FAISS_METADATA_PATH, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(f"FAISS index loaded: {self.index.ntotal} entries")
        else:
            logger.info("No FAISS index found — starting fresh.")

    def save(self):
        FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(FAISS_INDEX_PATH))
        with open(FAISS_METADATA_PATH, "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(f"FAISS index saved ({self.index.ntotal} entries)")

    # ── Building ──────────────────────────────────────────────
    def build_from_dataset(self, texts: list[str], labels: np.ndarray, batch_size: int = 64):
        """
        Encode all FAKE job texts and build the FAISS index.
        Only fake postings are stored.
        """
        fake_texts = [t for t, l in zip(texts, labels) if l == 1]
        fake_meta  = [{"label": 1, "text_snippet": t[:200]} for t in fake_texts]

        logger.info(f"Encoding {len(fake_texts)} fake job postings with SBERT...")
        embeddings = self.encoder.encode(
            fake_texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,  # cosine similarity via inner product
        )
        embeddings = np.array(embeddings, dtype=np.float32)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner Product = cosine (since normalized)
        self.index.add(embeddings)
        self.metadata = fake_meta

        self.save()
        logger.info(f"FAISS index built with {self.index.ntotal} fake job embeddings (dim={dim})")

    # ── Querying ──────────────────────────────────────────────
    def find_similar_fakes(self, text: str, top_k: int = 3) -> list[dict]:
        """
        Return top-K most similar fake jobs to the given text.

        Returns
        -------
        list of {similarity, text_snippet}
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = self.encoder.encode(
            [text],
            normalize_embeddings=True,
        ).astype(np.float32)

        distances, indices = self.index.search(query_embedding, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            results.append({
                "similarity": round(float(dist), 4),
                "text_snippet": self.metadata[idx].get("text_snippet", ""),
            })
        return results

    def similarity_boost(self, text: str) -> dict:
        """
        Check similarity against FAISS; return boost info.

        Returns
        -------
        {
          boosted: bool,
          similarity_score: float,
          message: str,
          top_match_snippet: str
        }
        """
        similar = self.find_similar_fakes(text, top_k=1)
        if not similar:
            return {"boosted": False, "similarity_score": 0.0, "message": "", "top_match_snippet": ""}

        top = similar[0]
        sim = top["similarity"]
        boosted = sim >= SIMILARITY_THRESHOLD

        message = (
            f"Similar to previously detected fake job ({int(sim*100)}% similarity)"
            if boosted else ""
        )

        return {
            "boosted": boosted,
            "similarity_score": round(sim, 4),
            "message": message,
            "top_match_snippet": top["text_snippet"],
        }

    # ── Adding new entries ────────────────────────────────────
    def add_entry(self, text: str, label: int):
        """Add a single confirmed fake to the index."""
        if label != 1:
            return  # Only store fake jobs

        embedding = self.encoder.encode(
            [text], normalize_embeddings=True
        ).astype(np.float32)

        if self.index is None:
            dim = embedding.shape[1]
            self.index = faiss.IndexFlatIP(dim)

        self.index.add(embedding)
        self.metadata.append({"label": 1, "text_snippet": text[:200]})
        self.save()


# ── Build Index Entry Point ──────────────────────────────────
if __name__ == "__main__":
    import pandas as pd
    df = pd.read_parquet(PROCESSED_DATA_DIR / "df_for_faiss.parquet")
    store = FAISSMemoryStore()
    store.build_from_dataset(
        texts=df["combined_text"].tolist(),
        labels=df["fraudulent"].values,
    )
