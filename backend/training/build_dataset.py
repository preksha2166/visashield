"""Merge public datasets + synthetic in-domain data into train/val/test splits.

Public sources (Hugging Face):
  ucirvine/sms_spam                               spam -> other_scam, ham -> legitimate
  victor/real-or-fake-fake-jobposting-prediction  (EMSCAD) fraudulent -> fake_job_task, real -> legitimate
  zefang-liu/phishing-email-dataset               phishing -> other_scam, safe -> legitimate
Synthetic: data/processed/synthetic.jsonl (training/generate_synthetic.py)

All text is passed through the same PII redactor used at inference time.
Usage: python -m training.build_dataset
"""
import json
import random
import re
from collections import Counter

from datasets import load_dataset

from app import config
from app.ingest.redact import redact

OUT_DIR = config.DATA_DIR / "processed"
CAPS = {"legitimate": 2800, "other_scam": 1300, "fake_job_task": 1200, "gov_impersonation": 10**9, "opt_employer_fraud": 10**9}


def _clean(text: str, limit: int) -> str:
    text = re.sub(r"#(URL|EMAIL|PHONE)_[0-9a-f]+#", lambda m: {"URL": "[link]", "EMAIL": "[email]", "PHONE": "[phone]"}[m.group(1)], text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def load_public(r: random.Random) -> list[dict]:
    rows = []
    sms = load_dataset("ucirvine/sms_spam", split="train")
    for x in sms:
        rows.append({"text": _clean(x["sms"], 600), "label": "other_scam" if str(x["label"]) == "1" else "legitimate", "channel": "sms", "source": "uci_sms_spam"})

    jobs = load_dataset("victor/real-or-fake-fake-jobposting-prediction", split="train")
    for x in jobs:
        parts = [x["title"], x["company_profile"], x["description"], x["requirements"], x["benefits"]]
        text = _clean(". ".join(p for p in parts if p and p != "None"), 1200)
        if len(text) < 40:
            continue
        rows.append({"text": text, "label": "fake_job_task" if str(x["fraudulent"]) == "1" else "legitimate", "channel": "job_post", "source": "emscad"})

    phish = load_dataset("zefang-liu/phishing-email-dataset", split="train")
    for x in phish:
        text = _clean(x["Email Text"] or "", 1500)
        if len(text) < 40 or text == "empty":
            continue
        rows.append({"text": text, "label": "other_scam" if x["Email Type"] == "Phishing Email" else "legitimate", "channel": "email", "source": "phishing_email"})
    return rows


def main(seed: int = 13):
    r = random.Random(seed)
    public = load_public(r)
    synthetic = [json.loads(l) for l in open(OUT_DIR / "synthetic.jsonl", encoding="utf-8")]

    # Keep every synthetic row; sample public rows per (source, label) so no source dominates.
    by_key: dict[tuple, list] = {}
    for row in public:
        by_key.setdefault((row["source"], row["label"]), []).append(row)
    quotas = {
        ("uci_sms_spam", "other_scam"): 747, ("uci_sms_spam", "legitimate"): 900,
        ("emscad", "fake_job_task"): 866, ("emscad", "legitimate"): 600,
        ("phishing_email", "other_scam"): 500, ("phishing_email", "legitimate"): 500,
    }
    sampled = []
    for key, items in by_key.items():
        r.shuffle(items)
        sampled += items[: quotas.get(key, 0)]

    rows, seen = [], set()
    for row in synthetic + sampled:
        row["text"], _ = redact(row["text"])
        k = row["text"].lower()
        if k in seen:
            continue
        seen.add(k)
        rows.append(row)

    by_label: dict[str, list] = {}
    for row in rows:
        by_label.setdefault(row["label"], []).append(row)
    splits = {"train": [], "val": [], "test": []}
    for label, items in by_label.items():
        r.shuffle(items)
        items = items[: CAPS[label]]
        n = len(items)
        n_val, n_test = int(n * 0.1), int(n * 0.1)
        splits["val"] += items[:n_val]
        splits["test"] += items[n_val : n_val + n_test]
        splits["train"] += items[n_val + n_test :]

    for name, items in splits.items():
        r.shuffle(items)
        with open(OUT_DIR / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for row in items:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{name}: {len(items)} {dict(Counter(x['label'] for x in items))}")
    print("sources (train):", dict(Counter(x["source"] for x in splits["train"])))


if __name__ == "__main__":
    main()
