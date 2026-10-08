"""Unit tests for the deterministic layers. Run from backend/: python -m pytest -q"""
import os

os.environ["ENABLE_RDAP"] = "0"

from app.actions import plan
from app.ingest.redact import redact
from app.signals.context import is_warning_notice
from app.signals.entities import claimed_agency, extract_entities
from app.signals.tactics import tag_tactics
from app.signals.verify import check_rules, lookalike_of, verify


def test_redacts_identifiers():
    text, counts = redact("SSN 123-45-6789, passport no: K1234567, SEVIS N0012345678, card 4111 1111 1111 1111")
    assert "123-45-6789" not in text and "K1234567" not in text and "N0012345678" not in text
    assert "4111" not in text
    assert counts == {"SSN": 1, "PASSPORT": 1, "SEVIS_ID": 1, "CARD": 1}


def test_redaction_keeps_ordinary_numbers():
    text, counts = redact("Pay $1,850 by Friday, call (212) 436-9315, order 12345")
    assert counts == {}
    assert "(212) 436-9315" in text


def test_lookalike_domains():
    assert lookalike_of("uscis-gov.help") == "uscis.gov"
    assert lookalike_of("dhs.gov.case-check.info") is not None
    assert lookalike_of("amzn-careers-hr.com") == "amazon.com"
    assert lookalike_of("uscis.gov") is None
    assert lookalike_of("studyinthestates.dhs.gov") is None
    assert lookalike_of("university.edu") is None


def test_mentioning_sevis_is_not_claiming_to_be_an_agency():
    assert claimed_agency("ISSS will update your SEVIS record.") is None
    assert claimed_agency("This is Officer Ross from ICE.") == "ICE"
    assert claimed_agency("USCIS field office compliance notice") == "USCIS"


def test_warning_sentences_do_not_count_as_tactics():
    warning = "Government agencies will never demand payment by phone or gift cards. If you receive one, hang up."
    assert "payment_demand" not in tag_tactics(warning)
    assert check_rules(warning) == []
    scam = "This is Officer Ross from ICE. Pay the bond with Google Play gift cards today or you will be deported."
    assert {"payment_demand", "fear_threat"} <= set(tag_tactics(scam))


def test_scam_denial_does_not_hide_the_scam():
    text = "This is Officer Ross from ICE. This is not a scam, pay the bond with gift cards today."
    assert check_rules(text), "a scammer saying 'this is not a scam' must not suppress the rules"


def test_school_scam_alert_is_a_warning_notice():
    alert = ("Subject: Scam alert\n\nStudents reported calls from people claiming to be ICE agents demanding gift cards. "
             "These calls are scams. Government agencies will never demand payment by phone.")
    assert is_warning_notice(alert)
    assert not is_warning_notice("This is Officer Ross from ICE. Pay $900 in gift cards now.")


def test_verification_signals():
    text = "From: USCIS Online <alerts@uscis-services.link>\nPay the $85 fee at http://uscis-services.link/verify"
    findings, feats = verify(text, extract_entities(text))
    assert feats["gov_claim_non_gov_domain"] == 1.0
    assert feats["risky_tld"] == 1.0
    assert feats["lookalike_domain"] == 1.0
    signals = {f.signal for f in findings}
    assert "gov_claim_non_gov_domain" in signals


def test_action_plan_has_safety_floor():
    steps = plan("gov_impersonation", "likely_scam", "paid")
    assert any("bank" in s.lower() for s in steps)
    assert any("reportfraud.ftc.gov" in s.lower() for s in steps)
    assert plan("legitimate", "likely_safe", "not_responded")[0].lower().startswith("this looks genuine")
