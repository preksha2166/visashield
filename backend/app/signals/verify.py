"""Deterministic verification checks: domains, sender auth, known numbers, official-rule violations.

Every check returns a `Finding` (signal id + user-facing text + optional source) and
sets a numeric feature consumed by the fusion model.
"""
import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

import httpx
import yaml
from rapidfuzz import fuzz

from app import config
from app.ingest.email_parser import EmailMeta
from app.schemas import Entities
from app.signals.context import first_affirmative_match, is_warning_notice
from app.signals.entities import host_of


@dataclass
class Finding:
    signal: str
    text: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None


# Official domains a scammer may imitate -> brand token used for containment checks.
PROTECTED = {
    "uscis.gov": "uscis",
    "ice.gov": "ice",
    "dhs.gov": "dhs",
    "studyinthestates.dhs.gov": "studyinthestates",
    "state.gov": "state",
    "cbp.gov": "cbp",
    "fbi.gov": "fbi",
    "ic3.gov": "ic3",
    "irs.gov": "irs",
    "ssa.gov": "ssa",
    "ftc.gov": "ftc",
    "e-verify.gov": "everify",
    "linkedin.com": "linkedin",
    "indeed.com": "indeed",
    "joinhandshake.com": "handshake",
    "paypal.com": "paypal",
    "chase.com": "chase",
    "bankofamerica.com": "bankofamerica",
    "wellsfargo.com": "wellsfargo",
    "amazon.com": "amazon",
    "google.com": "google",
    "microsoft.com": "microsoft",
}
# Tokens too short/common to use for containment (would fire on "office", "police"...).
_NO_CONTAINMENT = {"ice", "dhs", "state", "cbp", "fbi", "irs", "ssa", "ftc", "ic3"}
# Abbreviations scammers use in lookalike domains (e.g. "amzn-careers-hr.com").
BRAND_ALIASES = {"amzn": "amazon.com", "wellsfargo": "wellsfargo.com", "bofa": "bankofamerica.com", "msft": "microsoft.com", "linkedln": "linkedin.com", "sevp": "studyinthestates.dhs.gov", "sevis": "studyinthestates.dhs.gov"}
# Cheap top-level domains heavily used in phishing/scam campaigns; legitimate agencies,
# schools and large employers essentially never use them.
RISKY_TLDS = {"link", "support", "xyz", "top", "online", "live", "site", "info", "click", "help", "vip", "icu", "shop", "buzz", "rest", "cyou", "sbs", "monster", "work", "loan", "zip", "mov", "cfd"}

GOV_AGENCIES = {"ICE", "USCIS", "DHS", "SEVP / SEVIS", "CBP", "FBI", "IRS", "Social Security Administration", "U.S. Department of State", "U.S. Department of Labor"}

FREEMAIL = {
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com", "aol.com",
    "protonmail.com", "proton.me", "icloud.com", "gmx.com", "mail.com", "qq.com", "163.com", "yandex.com", "zoho.com",
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "rb.gy", "cutt.ly", "shorturl.at", "tiny.cc", "t.ly", "s.id"}
# Big sites we never RDAP-check or flag as new.
_WELL_KNOWN = set(PROTECTED) | FREEMAIL | {"zoom.us", "microsoftonline.com", "office.com", "okta.com", "workday.com", "myworkdayjobs.com", "greenhouse.io", "lever.co"}

_HOMOGLYPHS = [("rn", "m"), ("vv", "w"), ("0", "o"), ("1", "l"), ("3", "e"), ("5", "s"), ("7", "t"), ("@", "a")]
_MESSAGING = re.compile(r"\b(whatsapp|telegram|signal app|wechat|google hangouts|teams chat|text me at)\b", re.I)
_JOB_CONTEXT = re.compile(r"\b(job|position|role|interview|recruit\w*|hiring|offer|opt|employ\w*|salary|remote|part[- ]time)\b", re.I)

FEATURE_NAMES = [
    "gov_claim_non_gov_domain",
    "lookalike_domain",
    "new_domain",
    "url_shortener",
    "risky_tld",
    "freemail_official_claim",
    "email_auth_fail",
    "reply_to_mismatch",
    "spoofed_official_number",
    "moves_to_messaging_app",
    "rule_violations",
    "has_link",
    "warning_notice",
]


def registered_domain(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 3 and parts[-1] in {"gov", "edu"}:
        return ".".join(parts[-2:])
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in {"co", "com", "ac", "org", "gov", "net"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _normalize(label: str) -> str:
    label = label.lower().replace("-", "").replace("_", "")
    for a, b in _HOMOGLYPHS:
        label = label.replace(a, b)
    return label


def is_official(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in PROTECTED)


def lookalike_of(host: str) -> Optional[str]:
    """Return the official domain this host imitates, or None."""
    if not host or is_official(host):
        return None
    reg = registered_domain(host)
    reg_label = _normalize(reg.split(".")[0])
    full = _normalize(host.replace(".", ""))
    for official, token in PROTECTED.items():
        off_label = _normalize(official.split(".")[0])
        if len(off_label) >= 5 and reg_label != off_label and fuzz.ratio(reg_label, off_label) >= 85:
            return official
        if reg_label == off_label and reg != official:
            return official  # e.g. uscis.org, uscis-gov.com normalizes to "uscisgov" (handled below)
        if token not in _NO_CONTAINMENT and token in full:
            return official
        # "uscis-gov.com", "ice-gov.net", "dhs.gov.case-check.com"
        if re.search(rf"(^|[.-]){re.escape(token)}[.-]?gov([.-]|$)", host) and not host.endswith(".gov"):
            return official
    for alias, official in BRAND_ALIASES.items():
        if alias in full:
            return official
    if re.search(r"(^|[.-])(gov|edu)[.-]", host) and not host.endswith((".gov", ".edu")):
        return "a .gov or .edu domain"
    return None


@lru_cache(maxsize=512)
def domain_age_days(domain: str) -> Optional[int]:
    if not config.ENABLE_RDAP or domain in _WELL_KNOWN or domain.endswith((".gov", ".edu")):
        return None
    try:
        r = httpx.get(f"https://rdap.org/domain/{domain}", timeout=3.0, follow_redirects=True)
        if r.status_code != 200:
            return None
        for ev in r.json().get("events", []):
            if ev.get("eventAction") == "registration":
                created = datetime.fromisoformat(ev["eventDate"].replace("Z", "+00:00"))
                return (datetime.now(timezone.utc) - created).days
    except Exception:
        return None
    return None


@lru_cache(maxsize=1)
def load_rules() -> list[dict]:
    if not config.RULES_PATH.exists():
        return []
    rules = yaml.safe_load(config.RULES_PATH.read_text(encoding="utf-8")) or []
    for r in rules:
        r["_triggers"] = [re.compile(p, re.I) for p in r.get("triggers", [])]
        r["_requires"] = [re.compile(p, re.I) for p in r.get("requires_any", [])]
    return rules


@lru_cache(maxsize=1)
def load_known_numbers() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if config.KNOWN_NUMBERS_PATH.exists():
        with open(config.KNOWN_NUMBERS_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                digits = re.sub(r"\D", "", row["number"])[-10:]
                out[digits] = row
    return out


def check_rules(text: str) -> list[Finding]:
    findings = []
    for rule in load_rules():
        if not any(first_affirmative_match(rx, text) for rx in rule["_triggers"]):
            continue
        if rule["_requires"] and not any(rx.search(text) for rx in rule["_requires"]):
            continue
        findings.append(Finding(f"violates_official_rule:{rule['id']}", rule["statement"], rule.get("source_url"), rule.get("source_title")))
    return findings


def verify(text: str, entities: Entities, email: Optional[EmailMeta] = None) -> tuple[list[Finding], dict[str, float]]:
    findings: list[Finding] = []
    feats = {k: 0.0 for k in FEATURE_NAMES}

    hosts = {host_of(u) for u in entities.urls} | {e.rsplit("@", 1)[-1].lower() for e in entities.emails}
    if email:
        hosts |= {email.from_domain} | {host_of(u) for u in email.links}
    hosts.discard("")
    feats["has_link"] = float(bool(entities.urls) or bool(email and email.links))

    claims_gov = entities.claimed_agency in GOV_AGENCIES
    if claims_gov:
        # .edu is exempt: schools legitimately relay SEVIS/immigration information.
        non_gov = sorted(h for h in hosts if not h.endswith((".gov", ".edu")) and h not in SHORTENERS)
        if non_gov:
            feats["gov_claim_non_gov_domain"] = 1.0
            findings.append(Finding(
                "gov_claim_non_gov_domain",
                f"It claims to be from {entities.claimed_agency}, but uses a non-.gov address ({', '.join(non_gov[:3])}). Real US government websites and emails end in .gov.",
                "https://www.usa.gov/about-the-us-government", "USA.gov",
            ))

    for h in sorted(hosts):
        target = lookalike_of(h)
        if target:
            feats["lookalike_domain"] = 1.0
            findings.append(Finding("lookalike_domain", f"'{h}' looks like an imitation of {target}."))
            break

    if any(registered_domain(h) in SHORTENERS or h in SHORTENERS for h in hosts):
        feats["url_shortener"] = 1.0
        findings.append(Finding("url_shortener", "It uses a link shortener that hides where the link really goes."))

    risky = sorted(h for h in hosts if h.rsplit(".", 1)[-1] in RISKY_TLDS)
    if risky:
        feats["risky_tld"] = 1.0
        findings.append(Finding("risky_tld", f"The link uses a cheap domain ending often seen in scams ({risky[0]}). Real agencies use .gov, and schools use .edu."))

    for h in sorted({registered_domain(h) for h in hosts})[:3]:
        age = domain_age_days(h)
        if age is not None and age < 180:
            feats["new_domain"] = 1.0
            findings.append(Finding("new_domain", f"The domain {h} was registered only {age} days ago."))
            break

    sender_domains = {e.rsplit("@", 1)[-1].lower() for e in entities.emails}
    if email:
        sender_domains.add(email.from_domain)
    official_claim = claims_gov or bool(re.search(r"\b(hr|human resources|recruit\w*|talent acquisition|hiring manager|dso|international (student )?office)\b", text, re.I))
    if official_claim and sender_domains & FREEMAIL:
        feats["freemail_official_claim"] = 1.0
        findings.append(Finding("freemail_official_claim", "It claims to be an official or company recruiter but uses a free personal email account (like Gmail)."))

    if email:
        if email.auth_failed:
            feats["email_auth_fail"] = 1.0
            findings.append(Finding("email_auth_fail", f"The email failed sender authentication (SPF={email.spf or 'n/a'}, DKIM={email.dkim or 'n/a'}, DMARC={email.dmarc or 'n/a'})."))
        if email.reply_to_mismatch:
            feats["reply_to_mismatch"] = 1.0
            findings.append(Finding("reply_to_mismatch", f"Replies would go to {email.reply_to_domain}, not the sender's domain {email.from_domain}."))

    known = load_known_numbers()
    for p in entities.phone_numbers:
        row = known.get(re.sub(r"\D", "", p)[-10:])
        if row:
            feats["spoofed_official_number"] = 1.0
            findings.append(Finding("spoofed_official_number", row["note"], row.get("source_url") or None, row.get("source_title") or None))
            break

    if _MESSAGING.search(text) and _JOB_CONTEXT.search(text):
        feats["moves_to_messaging_app"] = 1.0
        findings.append(Finding("moves_to_messaging_app", "It moves the conversation to WhatsApp/Telegram or another chat app, a common pattern in fake job offers."))

    # Not a red flag: a message that warns ABOUT scams. Lowers the risk score in fusion.
    feats["warning_notice"] = float(is_warning_notice(text))

    rule_findings = check_rules(text)
    feats["rule_violations"] = float(min(len(rule_findings), 3))
    findings.extend(rule_findings)
    return findings, feats
