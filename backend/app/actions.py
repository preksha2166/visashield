"""Deterministic "what to do now" plans and report text.

These are the safety floor: the LLM may tailor and translate them, but the pipeline
always starts from these steps so critical advice can't be dropped or injected away.
"""
from datetime import date

from app.schemas import Entities
from app.signals.tactics import TACTIC_LABELS

_BASE = {
    "gov_impersonation": [
        "Stop responding. Hang up or don't reply, and don't call back any number they gave you.",
        "Do not pay anything or share personal details. US government agencies don't demand payment over the phone, by gift card, crypto, Zelle or wire transfer.",
        "Contact your school's international student office (DSO) using the phone number or email on your school's official website. They can check your actual SEVIS record.",
        "If you want to check with the agency itself, find the contact details yourself on its official .gov website. Never use contact details from the message.",
        "Save evidence: screenshots, phone numbers, email addresses, and the date and time.",
    ],
    "opt_employer_fraud": [
        "Don't pay any fee for a job, offer letter, I-983 training plan, E-Verify, or 'OPT sponsorship'. Legitimate employers don't charge you to work for them.",
        "Check the employer yourself: find its official website independently, and for STEM OPT confirm it's enrolled in E-Verify (search on e-verify.gov).",
        "Talk to your DSO before you report any employer in the SEVP Portal. Fake or unpaid 'employment' can put your status at risk.",
        "Save the messages, the offer, and any payment requests as evidence.",
    ],
    "fake_job_task": [
        "Don't send money, deposit a check, or buy equipment for this 'job'. Real employers never ask you to pay to start or to unlock earnings.",
        "Don't move the conversation to WhatsApp, Telegram or text. Verify the job on the company's official careers page.",
        "Report the posting or profile to the platform you found it on (LinkedIn, Handshake, Indeed) and tell your school's career office.",
        "Save screenshots of the chat, the job post and any payment details.",
    ],
    "other_scam": [
        "Don't pay or share personal details until you've verified the sender through an official channel you found yourself.",
        "For housing, never send a deposit before you have seen the place in person and verified the landlord. For tuition or fees, check your balance only in your school's official student portal.",
        "Save screenshots and contact details as evidence.",
    ],
    "legitimate": [
        "This looks genuine, but verify before acting: open the official website or app yourself instead of clicking links in the message.",
        "If it asks you to update SEVIS details, report OPT employment or sign documents, confirm with your DSO through your school's official contact page.",
        "If anything changes (pressure to pay, secrecy, a request for your SSN or passport), stop and check again.",
    ],
}

_PAID = [
    "Contact your bank, card issuer or payment app (Zelle, Venmo, Cash App) right now. Report fraud and ask them to stop or reverse the payment.",
    "If you paid with gift cards, contact the gift card company immediately with the card numbers and receipt. If you paid with crypto, contact the exchange you used.",
    "Report it at ReportFraud.ftc.gov and IC3.gov, and consider filing a local police report.",
    "Be careful of 'recovery' offers. Scammers often come back pretending to be police or lawyers who can get your money back for a fee.",
    "Tell your DSO what happened so they can support you.",
]

_SHARED = [
    "If you shared your SSN, go to IdentityTheft.gov for a recovery plan and place a free credit freeze with Equifax, Experian and TransUnion.",
    "Get an IRS Identity Protection PIN (IP PIN) so no one can file a tax return in your name.",
    "If you shared bank or account logins, change those passwords now, turn on two-factor authentication, and call your bank.",
    "If you shared passport or visa details, tell your DSO and contact your country's embassy or consulate for advice.",
    "Report it at ReportFraud.ftc.gov.",
]

REPORT_LINKS = "Report at https://reportfraud.ftc.gov and https://www.ic3.gov"


def plan(category: str, verdict: str, situation: str) -> list[str]:
    if verdict == "likely_safe":
        steps = list(_BASE["legitimate"])
    else:
        steps = list(_BASE.get(category if category != "legitimate" else "other_scam", _BASE["other_scam"]))
    if situation == "paid":
        steps = _PAID + steps[1:]
    elif situation == "shared_info":
        steps = _SHARED + steps[1:]
    elif verdict != "likely_safe":
        steps.append("Report it at ReportFraud.ftc.gov (and IC3.gov if it happened online), even if you didn't lose money. It helps warn others.")
    return steps


def report_text(category_label: str, tactics: list[str], entities: Entities, situation: str) -> str:
    who = f"someone claiming to be from {entities.claimed_agency}" if entities.claimed_agency else "someone I don't know"
    lines = [f"On {date.today():%B %d, %Y}, I received a message/call from {who}. I believe it is a scam ({category_label.lower()})."]
    if tactics:
        lines.append("Warning signs: " + "; ".join(TACTIC_LABELS[t].lower() for t in tactics if t in TACTIC_LABELS) + ".")
    if entities.payment_methods or entities.amounts:
        how = f" by {', '.join(entities.payment_methods)}" if entities.payment_methods else ""
        amt = f" of {', '.join(entities.amounts)}" if entities.amounts else ""
        lines.append(f"They asked for a payment{amt}{how}.")
    contacts = entities.phone_numbers + entities.emails + entities.urls
    if contacts:
        lines.append("Contact details they used: " + ", ".join(contacts[:8]) + ".")
    if situation == "paid":
        lines.append("I sent money: [amount, date, and how you paid].")
    elif situation == "shared_info":
        lines.append("I shared personal information: [what you shared].")
    else:
        lines.append("I did not send money or personal information.")
    return " ".join(lines)
