"""Risk fusion: combine classifier probabilities, tactic flags and verification signals.

A logistic regression trained by training/train_fusion.py (scam vs. legitimate).
Because it is linear, each feature's contribution (coef * value) is reported as a
reason, so every verdict is explainable. If no trained model exists, hand-set
weights with the same feature layout are used.
"""
import math
from functools import lru_cache

from app import config
from app.signals.tactics import TACTICS
from app.signals.verify import FEATURE_NAMES as VERIFY_FEATURES

PROB_FEATURES = [f"p_{c}" for c in config.CATEGORIES]
TACTIC_FEATURES = [f"tactic_{t}" for t in TACTICS]
FEATURES = PROB_FEATURES + TACTIC_FEATURES + VERIFY_FEATURES

_DEFAULT_WEIGHTS = {
    "p_gov_impersonation": 2.5, "p_opt_employer_fraud": 2.5, "p_fake_job_task": 2.5, "p_other_scam": 2.0, "p_legitimate": -2.5,
    "tactic_authority": 0.3, "tactic_urgency": 0.6, "tactic_fear_threat": 0.9, "tactic_secrecy": 1.4,
    "tactic_payment_demand": 1.3, "tactic_pii_request": 0.9, "tactic_advance_fee": 1.4, "tactic_too_good": 0.9,
    "gov_claim_non_gov_domain": 1.6, "lookalike_domain": 1.8, "new_domain": 1.0, "url_shortener": 0.6, "risky_tld": 0.8,
    "freemail_official_claim": 1.2, "email_auth_fail": 1.2, "reply_to_mismatch": 0.6, "spoofed_official_number": 1.5,
    "moves_to_messaging_app": 0.9, "rule_violations": 1.0, "has_link": 0.1, "warning_notice": -2.0,
}
_DEFAULT_BIAS = -1.6


def build_features(probs: dict[str, float], tactics: set[str], verify_feats: dict[str, float]) -> list[float]:
    row = [probs[c] for c in config.CATEGORIES]
    row += [1.0 if t in tactics else 0.0 for t in TACTICS]
    row += [verify_feats.get(k, 0.0) for k in VERIFY_FEATURES]
    return row


@lru_cache(maxsize=1)
def _load():
    if config.FUSION_PATH.exists():
        import joblib

        bundle = joblib.load(config.FUSION_PATH)
        if bundle.get("features") == FEATURES:
            return bundle["weights"], float(bundle["bias"]), f"trained (expert prior, lam={bundle.get('lam')})"
        print("[fusion] feature layout changed; retrain with training/train_fusion.py. Using default weights.")
    return _DEFAULT_WEIGHTS, _DEFAULT_BIAS, "default"


def fusion_info() -> str:
    return _load()[2]


def score(row: list[float]) -> tuple[float, dict[str, float]]:
    """Return (risk probability, per-feature contribution)."""
    weights, bias, _ = _load()
    contrib = {f: weights[f] * x for f, x in zip(FEATURES, row)}
    z = bias + sum(contrib.values())
    return 1 / (1 + math.exp(-z)), contrib
