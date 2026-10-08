"""Thin OpenAI-compatible chat client (Groq, Featherless, OpenRouter, Gemini...) returning parsed JSON."""
import json
import re
from functools import lru_cache
from typing import Optional

from app import config


def available() -> bool:
    return bool(config.LLM_API_KEY)


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL, timeout=config.LLM_TIMEOUT_S, max_retries=1)


def _parse_json(text: str) -> Optional[dict]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def chat_json(system: str, user: str, max_tokens: int = 900, temperature: float = 0.2) -> Optional[dict]:
    if not available():
        return None
    extra = {}
    if "gpt-oss" in config.LLM_MODEL:
        # Reasoning model: explanation writing doesn't need deep reasoning, and reasoning
        # tokens count against max_tokens (non-Latin scripts also use many tokens).
        extra = {"reasoning_effort": "low"}
        max_tokens += 1500
    try:
        resp = _client().chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=max_tokens,
            temperature=temperature,
            extra_body=extra or None,
        )
        if resp.choices[0].finish_reason == "length":
            print("[llm] response truncated (max_tokens)")
        return _parse_json(resp.choices[0].message.content or "")
    except Exception as e:
        print(f"[llm] request failed: {type(e).__name__}: {e}")
        return None
