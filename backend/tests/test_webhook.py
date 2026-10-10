"""Agentboxd webhook: signature checks, payload formats, and acknowledging before processing."""
import hashlib
import hmac
import json
import os
import time

os.environ["ENABLE_RDAP"] = "0"

from fastapi.testclient import TestClient

from app.integrations import agentboxd
from app.main import app

SECRET = "test-secret"


def _signed(body: dict, secret: str = SECRET, ts: int | None = None) -> tuple[bytes, dict]:
    raw = json.dumps(body).encode()
    ts = str(ts if ts is not None else int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
    return raw, {"X-Mailroom-Timestamp": ts, "X-Mailroom-Signature": sig, "Content-Type": "application/json"}


def _setup(monkeypatch) -> list:
    monkeypatch.setattr(agentboxd, "WEBHOOK_SECRET", SECRET)
    monkeypatch.setattr(agentboxd, "API_KEY", "key")
    monkeypatch.setattr(agentboxd, "INBOX_ID", "inbox")
    calls = []
    monkeypatch.setattr(agentboxd, "process_event", calls.append)
    return calls


def test_event_message_id_formats():
    assert agentboxd.event_message_id({"data": {"message_id": "m1"}}) == "m1"  # envelope payload
    assert agentboxd.event_message_id({"data": {"message": {"id": "m2"}}}) == "m2"  # full payload
    assert agentboxd.event_message_id({"data": {"message": {"extracted_text": "hi"}}}) is None


def test_webhook_queues_message(monkeypatch):
    calls = _setup(monkeypatch)
    raw, headers = _signed({"type": "message.received", "data": {"message_id": "m1"}})
    r = TestClient(app).post("/api/webhooks/agentboxd", content=raw, headers=headers)
    assert r.status_code == 200 and r.json() == {"ok": True, "queued": "m1"}
    assert calls == ["m1"]


def test_webhook_without_id_sweeps_unread(monkeypatch):
    calls = _setup(monkeypatch)
    raw, headers = _signed({"type": "message.received", "data": {"message": {"extracted_text": "hi"}}})
    r = TestClient(app).post("/api/webhooks/agentboxd", content=raw, headers=headers)
    assert r.status_code == 200 and r.json()["queued"] == "unread"
    assert calls == [None]


class _FakeClient:
    def __init__(self):
        self.posts = []

    def post(self, path, json):
        self.posts.append((path, json))
        return self

    def patch(self, path, json):
        return self

    def raise_for_status(self):
        return None


def test_quarantined_message_gets_reply(monkeypatch):
    monkeypatch.setattr(agentboxd, "INBOX_ID", "inbox")
    held = {
        "id": "m1", "from": "student@gmail.com", "labels": ["ai:phishing"],
        "withheld": {"state": "held", "reason": "phishing"}, "ai": {"risk": {"phishing": 0.98}},
    }
    client = _FakeClient()
    out = agentboxd.process_message(client, held)
    assert out["verdict"] == "quarantined" and out["replied"]
    path, body = client.posts[0]
    assert path == "/inboxes/inbox/messages/m1/reply" and "QUARANTINED AS LIKELY SCAM" in body["text"]


def test_webhook_rejects_bad_or_old_signatures(monkeypatch):
    calls = _setup(monkeypatch)
    body = {"type": "message.received", "data": {"message_id": "m1"}}
    client = TestClient(app)
    raw, headers = _signed(body, secret="wrong")
    assert client.post("/api/webhooks/agentboxd", content=raw, headers=headers).status_code == 401
    raw, headers = _signed(body, ts=int(time.time()) - 600)
    assert client.post("/api/webhooks/agentboxd", content=raw, headers=headers).status_code == 401
    assert calls == []
