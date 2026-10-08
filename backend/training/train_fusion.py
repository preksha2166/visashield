"""Train the risk-fusion model (scam vs. legitimate).

Features = classifier probabilities + tactic flags + verification signals (see
app/fusion/model.py). Trained on the VALIDATION split, which the text classifier never
saw, so its probabilities are realistic rather than memorized.

Model: logistic regression fitted as MAP with an expert prior and sign constraints:
  * Gaussian prior centred on the hand-set expert weights (app/fusion/model.py). Several
    verification signals (lookalike domains, failed SPF/DKIM, new domains, spoofed numbers)
    are rare or absent in the training data; with a plain LR they get ~0 weight and the
    model would ignore exactly the evidence that matters on new, real-world scams. With the
    prior, a signal keeps its expert weight unless the data says otherwise.
  * Sign constraints: red flags can't lower risk; "looks legitimate" signals can't raise it.
  * Classifier dropout: augmented copies where the classifier output is replaced by an
    uninformative prior, so the fit also learns from tactics and verification signals.
The prior strength is selected on the real-world DEV set (never on the test set).

Usage: python -m training.train_fusion
"""
import argparse
import json
import os
import random

os.environ["ENABLE_RDAP"] = "0"  # no network lookups: reproducible features

import app  # noqa: F401,E402  (loads torch before scikit-learn: Windows DLL order)

import joblib
import numpy as np
from scipy.optimize import minimize

from app import config
from app.fusion.model import _DEFAULT_BIAS, _DEFAULT_WEIGHTS, FEATURES, build_features
from app.ingest.redact import redact
from app.signals.classifier import get_classifier
from app.signals.entities import extract_entities
from app.signals.tactics import tag_tactics
from app.signals.verify import verify

NEGATIVE = {"p_legitimate", "warning_notice"}  # can only lower risk
BOUNDS = [(None, 0.0) if f in NEGATIVE else (0.0, None) for f in FEATURES]


def featurize(texts: list[str]) -> np.ndarray:
    redacted = [redact(t)[0] for t in texts]
    probs = get_classifier().predict_proba(redacted)
    rows = []
    for text, p in zip(redacted, probs):
        ents = extract_entities(text)
        tactics = set(tag_tactics(text))
        _, vfeats = verify(text, ents, None)
        rows.append(build_features(dict(zip(config.CATEGORIES, p.tolist())), tactics, vfeats))
    return np.array(rows)


def load(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    return [r["text"] for r in rows], np.array([0 if r["label"] == "legitimate" else 1 for r in rows])


def fit(X: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, float]:
    """MAP logistic regression: balanced log-loss + lam/2 * ||w - w_prior||^2, with sign bounds."""
    w0 = np.array([_DEFAULT_WEIGHTS[f] for f in FEATURES])
    sw = np.where(y == 1, len(y) / (2 * y.sum()), len(y) / (2 * (len(y) - y.sum())))

    def obj(theta):
        w, b = theta[:-1], theta[-1]
        z = X @ w + b
        p = 1 / (1 + np.exp(-z))
        loss = np.mean(sw * (np.logaddexp(0, z) - y * z))
        grad_z = sw * (p - y) / len(y)
        gw = X.T @ grad_z + lam * (w - w0)
        return loss + 0.5 * lam * np.sum((w - w0) ** 2), np.append(gw, grad_z.sum())

    theta0 = np.append(w0, _DEFAULT_BIAS)
    res = minimize(obj, theta0, jac=True, method="L-BFGS-B", bounds=BOUNDS + [(None, None)])
    return res.x[:-1], float(res.x[-1])


def f1_at_half(w, b, X, y):
    pred = (X @ w + b) >= 0
    tp, fp, fn = int((pred & (y == 1)).sum()), int((pred & (y == 0)).sum()), int((~pred & (y == 1)).sum())
    fpr = fp / max(1, int((y == 0).sum()))
    return (2 * tp / max(1, 2 * tp + fp + fn)), fpr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dropout", type=float, default=0.35)
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    texts, y = load(config.DATA_DIR / "processed" / "val.jsonl")
    X = featurize(texts)
    print(f"classifier: {get_classifier().name}; {len(y)} rows, {y.mean():.0%} scam")

    n_prob = len(config.CATEGORIES)
    Xa, ya = [X], [y]
    for _ in range(2):
        Xd = X.copy()
        for i in range(len(Xd)):
            if rng.random() < args.dropout:
                Xd[i, :n_prob] = 1 / n_prob
        Xa.append(Xd)
        ya.append(y)
    Xa, ya = np.vstack(Xa), np.concatenate(ya)

    dev_path = config.DATA_DIR / "eval" / "real_world_dev.jsonl"
    Xdev, ydev = featurize(load(dev_path)[0]), load(dev_path)[1]

    best = None
    print("\nprior strength selection on the real-world DEV set:")
    for lam in (0.003, 0.01, 0.03, 0.1, 0.3, 1.0):
        w, b = fit(Xa, ya, lam)
        f1_val, fpr_val = f1_at_half(w, b, X, y)
        f1_dev, fpr_dev = f1_at_half(w, b, Xdev, ydev)
        print(f"  lam={lam:<6} val F1={f1_val:.3f} FPR={fpr_val:.3f} | dev F1={f1_dev:.3f} FPR={fpr_dev:.3f}")
        score = f1_dev - fpr_dev  # prefer high F1 with low false positives
        if best is None or score > best[0] + 1e-9:
            best = (score, lam, w, b)
    _, lam, w, b = best
    print(f"\nselected lam={lam}")
    print("weights (prior -> fitted):")
    for f, wi in sorted(zip(FEATURES, w), key=lambda t: -abs(t[1])):
        print(f"  {f:28s} {_DEFAULT_WEIGHTS[f]:+.2f} -> {wi:+.3f}")
    print(f"  {'(bias)':28s} {_DEFAULT_BIAS:+.2f} -> {b:+.3f}")
    joblib.dump({"weights": dict(zip(FEATURES, w.tolist())), "bias": b, "features": FEATURES, "lam": lam,
                 "classifier": get_classifier().name}, config.FUSION_PATH)
    print(f"saved {config.FUSION_PATH}")


if __name__ == "__main__":
    main()
