"""Sentence context helpers shared by the tactic tagger and the rule engine.

A sentence that warns ABOUT a scam ("agencies will never ask for gift cards") is not
the scam itself, so pattern matches inside such sentences are ignored.
"""
import re

_WARNING_CUES = re.compile(
    r"\b(never|will not|won't|would not|do not pay|don't pay|do not send|don't send|scam|scams|scammers?|fraud alert|beware|be aware|report (it|them|this|suspicious)|not a legitimate|you are not in trouble)\b",
    re.I,
)
# Scammers deny being scams ("this is not a scam"); those phrases must not count as warnings.
_DENIALS = re.compile(r"\b(this )?(is )?(not|isn't|no) (a )?(scam|fraud)\b|\bnot scammers?\b|\bno scam\b", re.I)
_SENTENCE_END = re.compile(r"[.!?\n]")


def sentence_around(text: str, start: int, end: int) -> str:
    left = max((m.end() for m in _SENTENCE_END.finditer(text, 0, start)), default=0)
    right_m = _SENTENCE_END.search(text, end)
    return text[left : right_m.start() if right_m else len(text)]


def is_warning_sentence(sentence: str) -> bool:
    return bool(_WARNING_CUES.search(_DENIALS.sub(" ", sentence)))


_ALERT_HEADLINE = re.compile(r"^(subject:.*)?\b(scam|fraud|phishing) (alert|warning)\b|\b(alert|warning): .*\b(scam|impersonat\w*|fake|fraud)", re.I | re.M)


def is_warning_notice(text: str) -> bool:
    """True for messages whose purpose is to warn about scams (e.g. a school's scam alert)."""
    sentences = [s for s in _SENTENCE_END.split(text) if s.strip()]
    n_warning = sum(is_warning_sentence(s) for s in sentences)
    return n_warning >= 2 or (n_warning >= 1 and bool(_ALERT_HEADLINE.search(text)))


def first_affirmative_match(rx: re.Pattern, text: str) -> re.Match | None:
    """First match of rx that is not inside a warning sentence."""
    for m in rx.finditer(text):
        if not is_warning_sentence(sentence_around(text, m.start(), m.end())):
            return m
    return None
