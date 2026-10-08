"""Redact sensitive identifiers before any text leaves the machine (e.g. to the LLM API)."""
import re


def _luhn_ok(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# (label, pattern, flags). A pattern with a named group "keep" keeps that prefix
# (e.g. "passport no: ") and redacts only the identifier after it.
_PATTERNS = [
    ("SSN", r"\b(?!000|666|9\d\d)\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b", 0),
    ("SSN", r"(?P<keep>\b(?:ssn|social security(?: number| no\.?)?)[:#\s]{1,3})\d{9}\b", re.I),
    ("SEVIS_ID", r"\bN\d{10}\b", 0),
    ("A_NUMBER", r"\bA[- ]?\d{3}[- ]?\d{3}[- ]?\d{2,3}\b", 0),
    ("USCIS_RECEIPT", r"\b(?:IOE|EAC|WAC|LIN|SRC|NBC|MSC|YSC)\d{10}\b", re.I),
    ("PASSPORT", r"(?P<keep>\bpassport(?:\s*(?:no\.?|number|#))?[:\s]{1,3})(?=[A-Z0-9]*\d)[A-Z0-9]{6,9}\b", re.I),
    ("I94", r"(?P<keep>\bi-?94(?:\s*(?:no\.?|number|#))?[:\s]{1,3})\d{9,11}[A-Z0-9]?\b", re.I),
    ("ACCOUNT", r"(?P<keep>\b(?:account|acct|routing)(?:\s*(?:no\.?|number|#))?[:\s]{1,3})\d{6,17}\b", re.I),
]
_COMPILED = [(label, re.compile(p, f)) for label, p, f in _PATTERNS]
_CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Return (redacted_text, counts_by_type)."""
    counts: dict[str, int] = {}

    def bump(label: str) -> None:
        counts[label] = counts.get(label, 0) + 1

    out = text
    for label, rx in _COMPILED:
        def repl(m: re.Match, label=label) -> str:
            bump(label)
            keep = m.groupdict().get("keep") or ""
            return f"{keep}[REDACTED_{label}]"

        out = rx.sub(repl, out)

    def card_repl(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            bump("CARD")
            return "[REDACTED_CARD]"
        return m.group(0)

    out = _CARD.sub(card_repl, out)
    return out, counts
