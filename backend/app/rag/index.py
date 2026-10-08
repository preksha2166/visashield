"""Retrieval over the official-source knowledge base (data/kb/*.md).

Each `## section` of a KB file is one chunk, embedded with a small sentence-transformer
and stored in a FAISS inner-product index. Build with: python -m app.rag.index
"""
import json
import re
from functools import lru_cache

import numpy as np

from app import config

INDEX_FILE = config.RAG_DIR / "kb.faiss"
META_FILE = config.RAG_DIR / "kb_meta.json"


def _parse_kb_file(text: str) -> tuple[dict, str]:
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        text = text[m.end():]
    return meta, text


def load_chunks() -> list[dict]:
    chunks = []
    for path in sorted(config.KB_DIR.glob("*.md")):
        meta, body = _parse_kb_file(path.read_text(encoding="utf-8"))
        for section in re.split(r"\n(?=## )", "\n" + body):
            section = section.strip()
            if not section:
                continue
            heading, _, content = section.partition("\n")
            content = content.strip()
            if len(content) < 40:
                continue
            chunks.append({
                "title": meta.get("title", path.stem),
                "heading": heading.lstrip("# ").strip(),
                "url": meta.get("source_url", ""),
                "publisher": meta.get("publisher", ""),
                "text": content,
            })
    return chunks


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(config.EMBED_MODEL, device="cpu")


def embed(texts: list[str]) -> np.ndarray:
    # The int8 ONNX embedder (lite runtime) is used whenever it exists, both to build the
    # index and to embed queries, so index and queries always come from the same model.
    from app import onnx_models

    if onnx_models.available("embedder"):
        return onnx_models.embed(texts)
    return _embedder().encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype("float32")


def build() -> int:
    import faiss

    chunks = load_chunks()
    if not chunks:
        raise SystemExit(f"No KB chunks found in {config.KB_DIR}")
    vecs = embed([f"{c['heading']}. {c['text']}" for c in chunks])
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    config.RAG_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))
    META_FILE.write_text(json.dumps(chunks, indent=1), encoding="utf-8")
    return len(chunks)


@lru_cache(maxsize=1)
def _load():
    import faiss

    if not INDEX_FILE.exists():
        return None, []
    return faiss.read_index(str(INDEX_FILE)), json.loads(META_FILE.read_text(encoding="utf-8"))


def available() -> bool:
    return _load()[0] is not None


def retrieve(query: str, k: int = 4) -> list[dict]:
    index, chunks = _load()
    if index is None:
        return []
    scores, ids = index.search(embed([query]), k)
    return [dict(chunks[i], score=float(s)) for s, i in zip(scores[0], ids[0]) if i >= 0]


if __name__ == "__main__":
    print(f"Indexed {build()} chunks -> {INDEX_FILE}")
