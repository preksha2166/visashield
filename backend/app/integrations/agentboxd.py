"""Forward-to-check email flow via an Agentboxd inbox.

Students forward a suspicious email to the VisaShield inbox and get the verdict back as
a reply in the same thread. Two ways to receive mail:

  * Poller (works on a laptop, no public URL):  python -m app.integrations.agentboxd --poll
  * Webhook (deployed):  Agentboxd POSTs `message.received` to /api/webhooks/agentboxd,
    signed with HMAC-SHA256 (X-Mailroom-Signature over "<timestamp>.<raw body>").

Agentboxd also screens every inbound email for phishing and prompt injection; those
scores are shown in the reply as an independent second opinion (they don't change the
VisaShield verdict). Held/unscreened messages are included on purpose: suspicious mail
is exactly what students forward to us.
"""
import argparse
import hashlib
import hmac
import os
import re
import time
from typing import Any, Optional

import httpx
from fastapi import BackgroundTasks, HTTPException, Request

from app import config  # noqa: F401  (loads .env)
from app.pipeline import analyze
from app.schemas import AnalyzeResponse

API_KEY = os.getenv("AGENTBOXD_API_KEY", "")
BASE_URL = os.getenv("AGENTBOXD_BASE_URL", "https://api.agentboxd.com").rstrip("/")
INBOX_ID = os.getenv("AGENTBOXD_INBOX_ID", "")
INBOX_ADDRESS = os.getenv("AGENTBOXD_INBOX_ADDRESS", "").lower()
WEBHOOK_SECRET = os.getenv("AGENTBOXD_WEBHOOK_SECRET", "")
DONE_LABEL = "visashield-checked"

_VERDICT_TITLE = {"likely_scam": "LIKELY SCAM", "suspicious": "SUSPICIOUS", "likely_safe": "NO STRONG SCAM SIGNALS"}
_NO_REPLY = re.compile(r"(mailer-daemon|postmaster|no-?reply|noreply|bounce)", re.I)


def available() -> bool:
    return bool(API_KEY and INBOX_ID)


def _client() -> httpx.Client:
    return httpx.Client(base_url=f"{BASE_URL}/v1", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=20)


def _addr(value: Any) -> str:
    """Agentboxd address fields may be a string, {address,name} object, or a list of either."""
    if isinstance(value, list):
        return _addr(value[0]) if value else ""
    if isinstance(value, dict):
        return str(value.get("address") or value.get("email") or "")
    m = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", str(value or ""))
    return m.group(0) if m else ""


def _risk(msg: dict, key: str) -> Optional[float]:
    try:
        return float(((msg.get("ai") or {}).get("risk") or {}).get(key))
    except (TypeError, ValueError):
        return None


def message_text(msg: dict) -> str:
    """Body to analyze: the forwarded content, minus the forwarder's own address."""
    body = msg.get("extracted_text") or msg.get("text") or ""
    if not body and msg.get("html"):
        body = re.sub(r"<[^>]+>", " ", msg["html"])
    sender = _addr(msg.get("from")).lower()
    if sender:
        body = re.sub(re.escape(sender), "[forwarder]", body, flags=re.I)
    # Drop "To:/Cc:" lines of the forwarded header: they list the student, not the scammer.
    body = re.sub(r"(?im)^\s*(to|cc):.*$", "", body)
    subject = msg.get("subject") or ""
    subject = re.sub(r"^\s*((fwd?|fw|tr|wg)\s*:\s*)+", "", subject, flags=re.I)
    return f"Subject: {subject}\n\n{body.strip()}"


_URLISH = re.compile(r"\b(?:https?://\S+|www\.\S+|[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}(?:/\S*)?)", re.I)
_SAFE_SUFFIXES = (".gov", ".edu")


def defang(text: str) -> str:
    """hxxps://evil[.]com for links from the message; .gov/.edu sources we cite stay clickable."""
    def fix(m: re.Match) -> str:
        u = m.group(0).rstrip(".,;:!?)")
        tail = m.group(0)[len(u):]
        host = re.sub(r"^\w+://", "", u).split("/")[0].lower()
        if host.endswith(_SAFE_SUFFIXES) or "." not in host:
            return m.group(0)
        return re.sub(r"^http", "hxxp", u, flags=re.I).replace(".", "[.]") + tail
    return _URLISH.sub(fix, text)


def format_reply(res: AnalyzeResponse, phishing: Optional[float] = None, injection: Optional[float] = None) -> str:
    lines = [f"VisaShield result: {_VERDICT_TITLE[res.verdict]} ({res.risk_score:.0%} risk) - {res.category_label}", "", res.summary, ""]
    flags = [r for r in res.reasons if r.weight > 0][:5]
    if flags:
        lines.append("Red flags we found:")
        lines += [f"  - {defang(r.text)}" + (f" [source: {r.source_url}]" if r.source_url else "") for r in flags]
        lines.append("")
    lines.append("What to do now:")
    lines += [f"  {i}. {a}" for i, a in enumerate(res.actions, 1)]
    if phishing is not None or injection is not None:
        lines += ["", "Independent screening by Agentboxd (second opinion):"]
        if phishing is not None:
            lines.append(f"  - Phishing risk: {phishing:.0%}")
        if injection is not None:
            lines.append(f"  - Prompt-injection risk: {injection:.0%}")
    if res.report_text:
        lines += ["", "Ready-to-paste report for ReportFraud.ftc.gov / IC3.gov:", defang(res.report_text)]
    if res.sources:
        lines += ["", "Official sources:"] + [f"  - {s.title}: {s.url}" for s in res.sources[:4]]
    lines += [
        "",
        "Links from the message are shown disabled (hxxp, [.]) on purpose. Don't open them or call numbers from the message.",
        "VisaShield is a student hackathon prototype and can be wrong. When in doubt, contact your school's international "
        "student office (DSO) using the contact details on your school's official website.",
    ]
    return "\n".join(lines)


def should_skip(msg: dict) -> Optional[str]:
    sender = _addr(msg.get("from")).lower()
    if not sender:
        return "no sender"
    if sender == INBOX_ADDRESS:
        return "own message"
    if _NO_REPLY.search(sender) or sender.endswith("@agentboxd.com"):
        return "automated sender"
    if any(str(l).startswith("agentboxd:") for l in (msg.get("labels") or [])):
        return "agentboxd system message"
    if msg.get("direction") == "outbound" or msg.get("status") in {"sent", "queued", "delivered"}:
        return "outbound"
    if DONE_LABEL in (msg.get("labels") or []):
        return "already checked"
    return None


def _has_body(msg: dict) -> bool:
    return any((msg.get(k) or "").strip() for k in ("extracted_text", "text", "html"))


def format_quarantine_reply(msg: dict) -> str:
    """Agentboxd held the message and withheld its content: say so, never invent a verdict."""
    reason = ((msg.get("withheld") or {}).get("reason") or "suspicious content").replace("_", " ")
    phishing = _risk(msg, "phishing")
    risk = f" (phishing risk {phishing:.0%})" if phishing is not None else ""
    steps = [
        "Don't reply, click links, open attachments, or call numbers in the message.",
        "Don't pay anything or share personal details (SSN, passport, I-20, bank login).",
        "If it claims to be from a government agency, your school or an employer, contact them using details you find yourself on their official website. For anything about SEVIS, OPT or your status, ask your DSO.",
        "Report it at ReportFraud.ftc.gov (and IC3.gov if it happened online).",
    ]
    lines = [
        "VisaShield result: QUARANTINED AS LIKELY SCAM",
        "",
        f"Our email provider's security screening (Agentboxd) quarantined this message as {reason}{risk} before "
        "VisaShield could read it. Treat it as a scam until you've verified it through official channels.",
        "",
        "What to do now:",
    ]
    lines += [f"  {i}. {a}" for i, a in enumerate(steps, 1)]
    lines += [
        "",
        "To get a full VisaShield analysis, paste the message text at the VisaShield website.",
        "VisaShield is a student hackathon prototype and can be wrong. When in doubt, contact your school's international "
        "student office (DSO) using the contact details on your school's official website.",
    ]
    return "\n".join(lines)


def process_message(client: httpx.Client, msg: dict, send: bool = True) -> dict:
    skip = should_skip(msg)
    if skip:
        return {"id": msg.get("id"), "skipped": skip}
    if not _has_body(msg):
        if (msg.get("withheld") or {}).get("state") == "held" or (msg.get("screening") or {}).get("state") == "held":
            out = {"id": msg["id"], "verdict": "quarantined", "risk": _risk(msg, "phishing"), "reply_text": format_quarantine_reply(msg)}
        else:
            return {"id": msg.get("id"), "skipped": "empty message"}
    else:
        res = analyze(message_text(msg), "en", "not_responded")
        reply = format_reply(res, _risk(msg, "phishing"), _risk(msg, "injection"))
        out = {"id": msg["id"], "verdict": res.verdict, "risk": res.risk_score, "reply_text": reply}
    if send:
        inbox = msg.get("inbox_id") or INBOX_ID
        r = client.post(f"/inboxes/{inbox}/messages/{msg['id']}/reply", json={"text": out["reply_text"]})
        r.raise_for_status()
        client.patch(f"/messages/{msg['id']}", json={"is_read": True, "add_labels": [DONE_LABEL]}).raise_for_status()
        out["replied"] = True
    return out


_held_allowed = True  # flips off if the API key lacks the "messages:release" permission


def _message_params() -> dict:
    p = {"include_unscreened": "true"}
    if _held_allowed:
        p["include_held"] = "true"
    return p


def _get(client: httpx.Client, path: str, params: dict) -> httpx.Response:
    """GET that retries without include_held when the key lacks messages:release."""
    global _held_allowed
    r = client.get(path, params={**params, **_message_params()})
    if r.status_code == 403 and _held_allowed and "messages:release" in r.text:
        _held_allowed = False
        print("[agentboxd] key lacks messages:release; held (quarantined) messages will be skipped")
        r = client.get(path, params={**params, **_message_params()})
    r.raise_for_status()
    return r


def fetch_unread(client: httpx.Client) -> list[dict]:
    r = _get(client, f"/inboxes/{INBOX_ID}/messages", {"is_read": "false", "direction": "inbound", "limit": 25})
    return r.json().get("data", [])


def fetch_message(client: httpx.Client, msg_id: str) -> dict:
    return _get(client, f"/messages/{msg_id}", {}).json()


def poll(once: bool, interval: float, send: bool) -> None:
    if not available():
        raise SystemExit("Set AGENTBOXD_API_KEY and AGENTBOXD_INBOX_ID in .env")
    print(f"[agentboxd] watching {INBOX_ADDRESS or INBOX_ID} (send={send})")
    with _client() as client:
        while True:
            try:
                for msg in fetch_unread(client):
                    full = fetch_message(client, msg["id"])
                    result = process_message(client, full, send=send)
                    print(f"[agentboxd] {result.get('id')}: {result.get('skipped') or result['verdict']}")
                    if not send and "reply_text" in result:
                        print(result["reply_text"])
            except httpx.HTTPError as e:
                print(f"[agentboxd] error: {e}")
            if once:
                return
            time.sleep(interval)


def _verify_signature(raw: bytes, signature: str, timestamp: str) -> bool:
    if not (WEBHOOK_SECRET and signature and timestamp):
        return False
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except ValueError:
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def event_message_id(event: dict) -> Optional[str]:
    """Message id of a message.received event. Envelope payloads carry data.message_id; full
    payloads nest the message under data.message and don't document its id, so check both."""
    data = event.get("data") or {}
    return data.get("message_id") or (data.get("message") or {}).get("id") or data.get("id")


def process_event(msg_id: Optional[str]) -> None:
    """Webhook work, run after the response is sent. Without a message id, check every unread
    inbound message instead (the poller's sweep); already-checked messages are skipped."""
    try:
        with _client() as client:
            ids = [msg_id] if msg_id else [m["id"] for m in fetch_unread(client)]
            for i in ids:
                try:
                    result = process_message(client, fetch_message(client, i))
                    print(f"[agentboxd] {result.get('id')}: {result.get('skipped') or result['verdict']}")
                except Exception as e:  # log and move on to the next message
                    print(f"[agentboxd] {i}: error: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"[agentboxd] error: {type(e).__name__}: {e}")


async def handle_webhook(request: Request, background: BackgroundTasks) -> dict:
    raw = await request.body()
    if not _verify_signature(raw, request.headers.get("X-Mailroom-Signature", ""), request.headers.get("X-Mailroom-Timestamp", "")):
        raise HTTPException(401, "invalid signature")
    event = await request.json()
    if event.get("type") != "message.received" or not available():
        return {"ok": True, "ignored": event.get("type")}
    msg_id = event_message_id(event)
    # Agentboxd counts a delivery as failed after 10 s, and analysis + LLM + reply can take
    # longer, so acknowledge now and do the work in the background.
    background.add_task(process_event, msg_id)
    return {"ok": True, "queued": msg_id or "unread"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Poll the VisaShield Agentboxd inbox and reply with verdicts.")
    ap.add_argument("--poll", action="store_true", help="keep polling")
    ap.add_argument("--interval", type=float, default=15)
    ap.add_argument("--dry-run", action="store_true", help="analyze and print replies without sending")
    args = ap.parse_args()
    poll(once=not args.poll, interval=args.interval, send=not args.dry_run)
