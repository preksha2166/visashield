"""Central configuration: paths, labels and environment settings."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data"
KB_DIR = DATA_DIR / "kb"
RULES_PATH = KB_DIR / "rules.yaml"
KNOWN_NUMBERS_PATH = DATA_DIR / "known_numbers.csv"
EXAMPLES_PATH = DATA_DIR / "examples.json"

MODELS_DIR = BACKEND_DIR / "models"
CLASSIFIER_DIR = MODELS_DIR / "classifier"
BASELINE_PATH = MODELS_DIR / "baseline.joblib"
FUSION_PATH = MODELS_DIR / "fusion.joblib"
RAG_DIR = MODELS_DIR / "rag"
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

CATEGORIES = [
    "gov_impersonation",
    "opt_employer_fraud",
    "fake_job_task",
    "other_scam",
    "legitimate",
]
SCAM_CATEGORIES = CATEGORIES[:-1]
CATEGORY_LABELS = {
    "gov_impersonation": "Government impersonation",
    "opt_employer_fraud": "OPT / employer fraud",
    "fake_job_task": "Fake job or task scam",
    "other_scam": "Other scam",
    "legitimate": "Looks legitimate",
}

# LLM: any OpenAI-compatible provider. Defaults to Groq (free tier, open-weight models).
# Legacy FEATHERLESS_* names are still read.
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("FEATHERLESS_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("FEATHERLESS_BASE_URL") or "https://api.groq.com/openai/v1"
LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("FEATHERLESS_MODEL") or "openai/gpt-oss-120b"
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "45"))

# Network lookups (RDAP domain age). Disabled during training/eval for reproducibility.
ENABLE_RDAP = os.getenv("ENABLE_RDAP", "1") == "1"

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

VERDICT_SCAM = float(os.getenv("VERDICT_SCAM", "0.7"))
VERDICT_SUSPICIOUS = float(os.getenv("VERDICT_SUSPICIOUS", "0.4"))

MAX_INPUT_CHARS = 8000
