"""End-to-end analysis: redact -> extract -> classify -> verify -> fuse -> retrieve -> explain."""
import re
import time
from typing import Optional

from app import actions, config
from app.fusion import model as fusion
from app.ingest.email_parser import EmailMeta
from app.ingest.redact import redact
from app.llm import client as llm_client
from app.llm.explainer import explain
from app.rag import index as rag
from app.schemas import AnalyzeResponse, Reason, Source
from app.signals.classifier import classify
from app.signals.entities import extract_entities
from app.signals.tactics import TACTIC_LABELS, tag_tactics
from app.signals.verify import GOV_AGENCIES, verify

_OPT_RX = re.compile(r"\b(opt|stem opt|i-?983|e-?verify|ead|unemployment days?|cap-?gap|employer letter)\b", re.I)

_CATEGORY_CONTEXT = {
    "gov_impersonation": "Real immigration agencies contact you through official mail, official portals, or your school. Only your school's DSO manages your SEVIS record, and no US agency demands payment over the phone or asks you to keep it secret from your school.",
    "opt_employer_fraud": "Legitimate OPT and STEM OPT employers don't charge you for jobs, offer letters or training plans. STEM OPT employers must be enrolled in E-Verify, and your DSO can help you check an employer.",
    "fake_job_task": "Real employers interview you through official channels and never ask you to pay, deposit money, or buy equipment to start working or to unlock earnings.",
    "other_scam": "Scammers often copy real organizations. Verify through contact details you find yourself on the official website.",
    "legitimate": "We didn't find pressure tactics, unusual payment demands, or imitation links.",
}

_PROB_TEXT = {
    "p_gov_impersonation": "Its wording closely matches known government-impersonation scams.",
    "p_opt_employer_fraud": "Its wording closely matches known OPT / employer fraud.",
    "p_fake_job_task": "Its wording closely matches known fake-job and task scams.",
    "p_other_scam": "Its wording closely matches other known scams.",
}


def _verdict(score: float) -> str:
    if score >= config.VERDICT_SCAM:
        return "likely_scam"
    if score >= config.VERDICT_SUSPICIOUS:
        return "suspicious"
    return "likely_safe"


def _pick_category(probs: dict[str, float], verdict: str, agency: Optional[str], tactics: set[str], text: str) -> str:
    if verdict == "likely_safe":
        return "legitimate"
    scores = {c: probs[c] for c in config.SCAM_CATEGORIES}
    if agency in GOV_AGENCIES:
        scores["gov_impersonation"] += 0.15
    if _OPT_RX.search(text):
        scores["opt_employer_fraud"] += 0.1
    if tactics & {"advance_fee", "too_good"}:
        scores["fake_job_task"] += 0.05
    return max(scores, key=scores.get)


def _reasons(contrib: dict[str, float], findings, tactic_hits: dict[str, list[str]], probs: dict[str, float]) -> list[Reason]:
    by_signal: dict[str, list] = {}
    for f in findings:
        key = "rule_violations" if f.signal.startswith("violates_official_rule:") else f.signal
        by_signal.setdefault(key, []).append(f)

    out: list[Reason] = []
    for feat, w in contrib.items():
        if w <= 0.05:
            continue
        if feat in by_signal:
            items = by_signal[feat]
            for f in items:
                out.append(Reason(signal=f.signal, text=f.text, weight=round(w / len(items), 3), source_url=f.source_url, source_title=f.source_title))
        elif feat.startswith("tactic_"):
            t = feat.removeprefix("tactic_")
            snippet = tactic_hits.get(t, [""])[0]
            text = TACTIC_LABELS[t] + (f': "{snippet.strip()}"' if snippet else "")
            out.append(Reason(signal=t, text=text, weight=round(w, 3)))
        elif feat in _PROB_TEXT and probs[feat.removeprefix("p_")] >= 0.35:
            out.append(Reason(signal="text_classifier", text=f"{_PROB_TEXT[feat]} (model confidence {probs[feat.removeprefix('p_')]:.0%})", weight=round(w, 3)))
    out.sort(key=lambda r: r.weight, reverse=True)
    return out[:8]


def _fallback_text(verdict: str, category: str, category_label: str, reasons: list[Reason]) -> tuple[str, str]:
    if verdict == "likely_scam":
        summary = f"This is very likely a scam ({category_label.lower()}). Don't respond, pay, or share personal information."
    elif verdict == "suspicious":
        summary = "This message has warning signs. Treat it as a possible scam until you verify it through official channels."
    else:
        summary = "We didn't find strong scam signals, but verify through official channels before you act."
    parts = []
    if reasons:
        parts.append("We flagged this because: " + "; ".join(r.text.rstrip(".") for r in reasons[:4]) + ".")
    parts.append(_CATEGORY_CONTEXT[category])
    return summary, "\n\n".join(parts)


def analyze(
    text: str,
    language: str = "en",
    situation: str = "not_responded",
    email: Optional[EmailMeta] = None,
    extracted_text: Optional[str] = None,
    use_llm: bool = True,
) -> AnalyzeResponse:
    t0 = time.perf_counter()
    text = text[: config.MAX_INPUT_CHARS]
    redacted, _ = redact(text)

    entities = extract_entities(redacted)
    tactic_hits = tag_tactics(redacted)
    tactics = set(tactic_hits)
    probs = classify(redacted)
    findings, vfeats = verify(redacted, entities, email)

    row = fusion.build_features(probs, tactics, vfeats)
    risk, contrib = fusion.score(row)
    verdict = _verdict(risk)
    category = _pick_category(probs, verdict, entities.claimed_agency, tactics, redacted)
    category_label = config.CATEGORY_LABELS[category]
    reasons = _reasons(contrib, findings, tactic_hits, probs) if verdict != "likely_safe" else [
        r for r in _reasons(contrib, findings, tactic_hits, probs) if r.weight >= 0.5
    ]

    retrieved = []
    if rag.available():
        query = f"{category_label}. " + " ".join(TACTIC_LABELS[t] for t in sorted(tactics)) + ". " + redacted[:400]
        retrieved = rag.retrieve(query, k=4)
    sources, seen = [], set()
    for r in reasons:
        if r.source_url and r.source_url not in seen:
            seen.add(r.source_url)
            sources.append(Source(title=r.source_title or r.source_url, url=r.source_url))
    for c in retrieved:
        if c["url"] and c["url"] not in seen:
            seen.add(c["url"])
            sources.append(Source(title=f"{c['title']}", url=c["url"], snippet=c["text"][:240]))

    steps = actions.plan(category, verdict, situation)
    summary, explanation = _fallback_text(verdict, category, category_label, reasons)
    llm_used = False
    if use_llm and llm_client.available():
        out = explain(redacted, verdict, risk, category_label, [r.text for r in reasons], retrieved, steps, situation, language)
        if out:
            llm_used = True
            summary, explanation, steps = out["summary"], out["explanation"] or explanation, out["actions"]
            for flag in out["extra_red_flags"]:
                reasons.append(Reason(signal="llm_observation", text=flag, weight=0.05))  # shown as a minor red flag; never affects the score

    report = actions.report_text(category_label, sorted(tactics), entities, situation) if verdict != "likely_safe" else None

    return AnalyzeResponse(
        verdict=verdict,
        risk_score=round(risk, 4),
        category=category,
        category_label=category_label,
        category_probs={k: round(v, 4) for k, v in probs.items()},
        summary=summary,
        explanation=explanation,
        reasons=reasons,
        tactics=sorted(tactics),
        entities=entities,
        actions=steps,
        report_text=report,
        sources=sources[:6],
        language=language if llm_used else "en",
        llm_used=llm_used,
        redacted_text=redacted,
        extracted_text=extracted_text,
        latency_ms=int((time.perf_counter() - t0) * 1000),
    )
