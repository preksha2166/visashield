"""Regex entity extraction: phones, URLs, emails, payment methods, amounts, claimed agency.

Always runs (no network); the LLM extractor, when available, adds to these results.
"""
import re
from urllib.parse import urlparse

from app.schemas import Entities

_PHONE = re.compile(r"(?<![\w/])(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_URL = re.compile(
    r"\b(?:https?://|www\.)[^\s<>\"')]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|info|xyz|top|site|online|live|co|us|io|me|gov|edu|app|link|click|support|help|vip|cc|biz|ly)(?:/[^\s<>\"')]*)?",
    re.I,
)
_AMOUNT = re.compile(r"(?:\$|usd\s?)\s?\d[\d,]*(?:\.\d{2})?|\b\d[\d,]*(?:\.\d{2})?\s?(?:dollars|usd|usdt)\b", re.I)

PAYMENT_METHODS = {
    "gift card": r"gift ?cards?|itunes|google play card|apple card|steam card|amazon card",
    "cryptocurrency": r"bitcoin|btc\b|crypto|usdt|tether|ethereum|wallet address",
    "bitcoin ATM": r"(bitcoin|crypto|btc) atm",
    "wire transfer": r"wire transfer|western union|moneygram",
    "Zelle": r"\bzelle\b",
    "Venmo": r"\bvenmo\b",
    "Cash App": r"cash ?app",
    "PayPal": r"\bpaypal\b",
    "check deposit": r"(deposit|cash) (the|this|a) check|mobile deposit",
    "cash": r"\bin cash\b|cash pickup|courier",
}
_PAY_RX = {k: re.compile(v, re.I) for k, v in PAYMENT_METHODS.items()}

AGENCIES = {
    "ICE": r"\bice\b|immigration and customs enforcement",
    "USCIS": r"\buscis\b|citizenship and immigration services",
    "DHS": r"\bdhs\b|homeland security",
    "SEVP / SEVIS": r"\bsevp\b|\bsevis\b",
    "CBP": r"\bcbp\b|customs and border",
    "FBI": r"\bfbi\b|federal bureau of investigation",
    "IRS": r"\birs\b|internal revenue",
    "Social Security Administration": r"\bssa\b|social security administration",
    "U.S. Department of State": r"department of state|state department|\bembassy\b|\bconsulate\b",
    "Police": r"\bpolice\b|sheriff",
    "U.S. Department of Labor": r"department of labor|\bdol\b",
}
_AGENCY_RX = {k: re.compile(v, re.I) for k, v in AGENCIES.items()}
# Mentioning an agency ("ISSS will update your SEVIS record") is not claiming to be it.
_CLAIM_BEFORE = re.compile(r"(this is|i am|i'm|im|calling (you )?from|call from|message from|notice from|on behalf of|officer|agent|inspector|representing|we are|from the|from)\W+(\w+\W+){0,6}$", re.I)
_CLAIM_AFTER = re.compile(r"^\W*(\w+\W+){0,2}(officer|agent|inspector|office|field office|department|division|headquarters|enforcement|notice|alert|case|investigation|unit|official)\b", re.I)


def claimed_agency(text: str) -> str | None:
    for name, rx in _AGENCY_RX.items():
        for m in rx.finditer(text):
            before = text[max(0, m.start() - 60) : m.start()]
            after = text[m.end() : m.end() + 40]
            if _CLAIM_BEFORE.search(before) or _CLAIM_AFTER.search(after):
                return name
    return None


def _format_phone(raw: str) -> str:
    d = re.sub(r"\D", "", raw)[-10:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}"


def _clean_url(u: str) -> str:
    return u.rstrip(".,;:!?")


def host_of(url_or_domain: str) -> str:
    u = url_or_domain if "://" in url_or_domain else "http://" + url_or_domain
    try:
        host = urlparse(u).hostname or ""
    except ValueError:
        host = ""
    return host.lower().removeprefix("www.")


def extract_entities(text: str) -> Entities:
    emails = sorted(set(_EMAIL.findall(text)))
    email_domains = {e.rsplit("@", 1)[-1].lower() for e in emails}

    urls = []
    for m in _URL.finditer(text):
        start = m.start()
        if start > 0 and text[start - 1] == "@":
            continue  # domain part of an email address
        u = _clean_url(m.group(0))
        if host_of(u) in email_domains and "/" not in u and "://" not in u:
            continue
        urls.append(u)

    phones = sorted({_format_phone(p) for p in _PHONE.findall(text) if len(re.sub(r"\D", "", p)) >= 10})

    payments = [name for name, rx in _PAY_RX.items() if rx.search(text)]

    return Entities(
        claimed_agency=claimed_agency(text),
        phone_numbers=phones,
        urls=sorted(set(urls)),
        emails=emails,
        payment_methods=payments,
        amounts=sorted(set(a.strip() for a in _AMOUNT.findall(text)))[:10],
    )
