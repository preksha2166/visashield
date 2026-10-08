"""Scam-category text classifier.

Loads the fine-tuned transformer from models/classifier if present, otherwise the
TF-IDF baseline from models/baseline.joblib, otherwise returns a uniform prior.
"""
from functools import lru_cache

import numpy as np

from app import config


class _Uniform:
    name = "none"

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        return np.full((len(texts), len(config.CATEGORIES)), 1 / len(config.CATEGORIES))


class _Baseline:
    name = "tfidf-logreg"

    def __init__(self):
        import joblib

        self.pipe = joblib.load(config.BASELINE_PATH)
        self.order = [list(self.pipe.classes_).index(c) for c in config.CATEGORIES]

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        return self.pipe.predict_proba(texts)[:, self.order]


class _Transformer:
    def __init__(self):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(config.CLASSIFIER_DIR)
        self.model = AutoModelForSequenceClassification.from_pretrained(config.CLASSIFIER_DIR).eval()
        id2label = self.model.config.id2label
        self.order = [next(int(i) for i, l in id2label.items() if l == c) for c in config.CATEGORIES]
        self.name = f"transformer:{self.model.config.model_type}-finetuned"

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        out = []
        with self.torch.no_grad():
            for i in range(0, len(texts), 32):
                enc = self.tok(texts[i : i + 32], truncation=True, max_length=192, padding=True, return_tensors="pt")
                logits = self.model(**enc).logits
                out.append(self.torch.softmax(logits, -1).numpy())
        return np.concatenate(out)[:, self.order]


class _Onnx:
    name = "onnx:distilbert-finetuned-int8"

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        from app import onnx_models

        return onnx_models.classify_proba(texts)


@lru_cache(maxsize=1)
def get_classifier():
    from app import onnx_models

    if onnx_models.available("classifier") and (onnx_models.use_onnx() or not (config.CLASSIFIER_DIR / "config.json").exists()):
        return _Onnx()
    if (config.CLASSIFIER_DIR / "config.json").exists():
        try:
            return _Transformer()
        except Exception as e:  # pragma: no cover - fall through to baseline
            print(f"[classifier] failed to load transformer: {e}")
    if config.BASELINE_PATH.exists():
        return _Baseline()
    return _Uniform()


def classify(text: str) -> dict[str, float]:
    probs = get_classifier().predict_proba([text])[0]
    return {c: float(p) for c, p in zip(config.CATEGORIES, probs)}
