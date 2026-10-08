"""Lite runtime: int8 ONNX models served with onnxruntime + tokenizers (no PyTorch).

Built by training/export_onnx.py. Used when PyTorch isn't installed (e.g. the 512 MB
Render deploy) or when VISASHIELD_RUNTIME=onnx.
"""
import os
from functools import lru_cache

import numpy as np

from app import config


def use_onnx() -> bool:
    if os.getenv("VISASHIELD_RUNTIME", "").lower() == "onnx":
        return True
    try:
        import torch  # noqa: F401
    except ImportError:
        return True
    return False


class _Encoder:
    def __init__(self, model: str, tokenizer: str, max_len: int):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = int(os.getenv("ONNX_THREADS", "2"))
        self.sess = ort.InferenceSession(str(config.ONNX_DIR / model), opts, providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}
        self.tok = Tokenizer.from_file(str(config.ONNX_DIR / tokenizer))
        self.tok.enable_truncation(max_length=max_len)
        self.tok.enable_padding()

    def run(self, texts: list[str]) -> tuple[np.ndarray, np.ndarray]:
        enc = self.tok.encode_batch(texts)
        feed = {
            "input_ids": np.array([e.ids for e in enc], dtype=np.int64),
            "attention_mask": np.array([e.attention_mask for e in enc], dtype=np.int64),
        }
        if "token_type_ids" in self.inputs:
            feed["token_type_ids"] = np.array([e.type_ids for e in enc], dtype=np.int64)
        return self.sess.run(None, feed)[0], feed["attention_mask"]


@lru_cache(maxsize=1)
def classifier() -> _Encoder:
    return _Encoder("classifier.onnx", "classifier_tokenizer.json", 192)


@lru_cache(maxsize=1)
def classifier_labels() -> list[str]:
    return (config.ONNX_DIR / "classifier_labels.txt").read_text(encoding="utf-8").split("\n")


@lru_cache(maxsize=1)
def embedder() -> _Encoder:
    return _Encoder("embedder.onnx", "embedder_tokenizer.json", 256)


def available(kind: str) -> bool:
    return (config.ONNX_DIR / f"{kind}.onnx").exists()


def classify_proba(texts: list[str]) -> np.ndarray:
    """Softmax probabilities in config.CATEGORIES order."""
    out = []
    for i in range(0, len(texts), 32):
        logits, _ = classifier().run(texts[i : i + 32])
        e = np.exp(logits - logits.max(-1, keepdims=True))
        out.append(e / e.sum(-1, keepdims=True))
    probs = np.concatenate(out)
    order = [classifier_labels().index(c) for c in config.CATEGORIES]
    return probs[:, order]


def embed(texts: list[str]) -> np.ndarray:
    """Mean-pooled, L2-normalized sentence embeddings (all-MiniLM-L6-v2 recipe)."""
    out = []
    for i in range(0, len(texts), 64):
        hidden, mask = embedder().run(texts[i : i + 64])
        m = mask[..., None].astype(np.float32)
        pooled = (hidden * m).sum(1) / np.clip(m.sum(1), 1e-9, None)
        out.append(pooled / np.linalg.norm(pooled, axis=1, keepdims=True))
    return np.concatenate(out).astype("float32")
