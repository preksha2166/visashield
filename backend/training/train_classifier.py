"""Fine-tune a transformer (default DistilBERT) for 5-class scam categorization.

Runs on CPU (slow but fine for ~5k short texts) or GPU (e.g. Google Colab T4).
Usage: python -m training.train_classifier --epochs 3
"""
import argparse
import json
import random
import time

import numpy as np
import torch
from sklearn.metrics import classification_report, f1_score
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from app import config

PROC = config.DATA_DIR / "processed"


def load(split):
    rows = [json.loads(l) for l in open(PROC / f"{split}.jsonl", encoding="utf-8")]
    return [r["text"] for r in rows], [config.CATEGORIES.index(r["label"]) for r in rows]


def batches(tok, texts, labels, bs, max_len, shuffle):
    idx = list(range(len(texts)))
    if shuffle:
        random.shuffle(idx)
    for i in range(0, len(idx), bs):
        b = idx[i : i + bs]
        enc = tok([texts[j] for j in b], truncation=True, max_length=max_len, padding=True, return_tensors="pt")
        enc["labels"] = torch.tensor([labels[j] for j in b])
        yield enc


@torch.no_grad()
def predict(model, tok, texts, max_len, device, bs=64):
    model.eval()
    out = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i : i + bs], truncation=True, max_length=max_len, padding=True, return_tensors="pt").to(device)
        out.append(torch.softmax(model(**enc).logits, -1).cpu().numpy())
    return np.concatenate(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="distilbert-base-uncased")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=4e-5)
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_num_threads(max(1, torch.get_num_threads()))
    print(f"device={device} threads={torch.get_num_threads()} model={args.model}")

    Xtr, ytr = load("train")
    Xva, yva = load("val")
    Xte, yte = load("test")

    id2label = dict(enumerate(config.CATEGORIES))
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(config.CATEGORIES), id2label=id2label, label2id={v: k for k, v in id2label.items()}
    ).to(device)

    counts = np.bincount(ytr, minlength=len(config.CATEGORIES))
    weights = torch.tensor(len(ytr) / (len(counts) * counts), dtype=torch.float).to(device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)

    steps = args.epochs * ((len(Xtr) + args.bs - 1) // args.bs)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)

    best = -1.0
    for epoch in range(args.epochs):
        model.train()
        t0, total, n = time.time(), 0.0, 0
        for step, enc in enumerate(batches(tok, Xtr, ytr, args.bs, args.max_len, True)):
            enc = enc.to(device)
            labels = enc.pop("labels")
            loss = loss_fn(model(**enc).logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            total += loss.item()
            n += 1
            if step % 50 == 0:
                print(f"epoch {epoch + 1} step {step} loss {total / n:.4f} ({time.time() - t0:.0f}s)", flush=True)
        pva = predict(model, tok, Xva, args.max_len, device).argmax(1)
        f1 = f1_score(yva, pva, average="macro")
        print(f"epoch {epoch + 1} done in {time.time() - t0:.0f}s, val macro-F1 {f1:.4f}", flush=True)
        if f1 > best:
            best = f1
            config.CLASSIFIER_DIR.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(config.CLASSIFIER_DIR)
            tok.save_pretrained(config.CLASSIFIER_DIR)
            print(f"saved best model -> {config.CLASSIFIER_DIR}")

    model = AutoModelForSequenceClassification.from_pretrained(config.CLASSIFIER_DIR).to(device)
    pte = predict(model, tok, Xte, args.max_len, device).argmax(1)
    print(classification_report(yte, pte, target_names=config.CATEGORIES, digits=3))


if __name__ == "__main__":
    main()
