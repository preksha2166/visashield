"""TF-IDF + logistic regression baseline. Usage: python -m training.train_baseline"""
import json

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.pipeline import FeatureUnion, Pipeline

from app import config

PROC = config.DATA_DIR / "processed"


def load(split: str):
    rows = [json.loads(l) for l in open(PROC / f"{split}.jsonl", encoding="utf-8")]
    return [r["text"] for r in rows], [r["label"] for r in rows]


def main():
    Xtr, ytr = load("train")
    Xte, yte = load("test")
    pipe = Pipeline([
        ("tfidf", FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=60000)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True, max_features=80000)),
        ])),
        ("clf", LogisticRegression(max_iter=2000, C=8.0, class_weight="balanced")),
    ])
    pipe.fit(Xtr, ytr)
    print(classification_report(yte, pipe.predict(Xte), digits=3))
    config.MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(pipe, config.BASELINE_PATH)
    print(f"saved {config.BASELINE_PATH}")


if __name__ == "__main__":
    main()
