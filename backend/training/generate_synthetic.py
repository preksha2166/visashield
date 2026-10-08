"""Compositional generator for in-domain synthetic training data.

No public dataset covers scams aimed at international students (fake ICE/USCIS/SEVIS
calls, OPT employer fraud), so we generate them from slot pools and many templates,
together with HARD NEGATIVES: genuine DSO reminders, USCIS notices, recruiter emails,
bank alerts and school scam-warnings that share vocabulary with the scams.

Output: data/processed/synthetic.jsonl  ({"text", "label", "channel", "source": "synthetic"})
Optional LLM paraphrasing: see training/paraphrase_llm.py.

Usage: python -m training.generate_synthetic --n-per-class 700 --seed 7
"""
import argparse
import json
import random
from pathlib import Path

from app import config

OUT = config.DATA_DIR / "processed" / "synthetic.jsonl"

FIRST = ["Daniel", "Michael", "Sarah", "James", "Linda", "Robert", "Kevin", "Angela", "David", "Steven", "Maria", "Brian", "Jennifer", "Mark", "Lisa", "Wei", "Priya", "Carlos", "Emily", "Jason"]
LAST = ["Ross", "Miller", "Johnson", "Carter", "Lopez", "Anderson", "Thompson", "Brooks", "Walker", "Reed", "Hughes", "Chen", "Patel", "Garcia", "Nguyen", "Wright", "Bennett", "Hayes", "Price", "Coleman"]
STUDENT = ["Ananya", "Rahul", "Mei", "Jiho", "Arjun", "Fatima", "Minh", "Sneha", "Kenji", "Lucas", "Aisha", "Ravi", "Yuna", "Omar", "Divya", "Hao", "Preeti", "Tuan"]
SCHOOLS = ["State University", "the university", "your school", "Northbridge University", "Lakeside College", "Westfield Institute of Technology", "City University"]
CITIES = ["New York", "Boston", "Chicago", "Houston", "San Jose", "Newark", "Dallas", "Seattle", "Atlanta", "Los Angeles"]

AGENCIES = [
    ("U.S. Immigration and Customs Enforcement", "ICE"),
    ("Immigration and Customs Enforcement", "ICE"),
    ("USCIS", "USCIS"),
    ("U.S. Citizenship and Immigration Services", "USCIS"),
    ("the Department of Homeland Security", "DHS"),
    ("Homeland Security Investigations", "HSI"),
    ("the Student and Exchange Visitor Program (SEVP)", "SEVP"),
    ("U.S. Customs and Border Protection", "CBP"),
    ("the FBI", "FBI"),
    ("the {city} Police Department", "police"),
    ("the IRS", "IRS"),
    ("the Social Security Administration", "SSA"),
    ("the U.S. Department of State visa office", "DOS"),
    ("the Chinese Consulate in {city}", "consulate"),
    ("the Embassy of India", "embassy"),
]
TITLES = ["Officer", "Agent", "Special Agent", "Inspector", "Deputy", "Sergeant", "Case Officer", "Senior Officer", "Field Agent"]
PROBLEMS = [
    "your SEVIS record has been flagged for termination",
    "your SEVIS status shows a violation and will be terminated",
    "there are discrepancies in your I-94 and visa records",
    "your F-1 visa has been flagged for fraudulent documents",
    "errors were found in your OPT application and EAD",
    "your passport was used to open bank accounts linked to money laundering",
    "a package in your name containing illegal items was seized at customs",
    "you missed a mandatory immigration identity verification",
    "your nonresident tax filing has errors and you owe back taxes",
    "your Social Security number was suspended due to suspicious activity",
    "your name came up in an identity fraud investigation",
    "your student visa status is under review for unauthorized employment",
    "your address on file does not match and your status is now invalid",
    "your STEM OPT extension was denied because of employer fraud",
]
THREATS = [
    "you will be deported within 48 hours",
    "a warrant will be issued for your arrest today",
    "your visa will be cancelled permanently",
    "you will be placed in removal proceedings",
    "your SEVIS record will be terminated and you must leave the country",
    "officers will come to your address to detain you",
    "you will be banned from re-entering the United States for 10 years",
    "your OPT and EAD will be revoked",
    "your bank accounts will be frozen",
    "criminal charges will be filed against you",
]
PAYMENTS = [
    "Google Play gift cards", "Apple gift cards", "Target gift cards", "a Bitcoin ATM", "cryptocurrency (USDT)",
    "Zelle", "a wire transfer", "Western Union", "Cash App", "MoneyGram", "Venmo", "cash handed to our courier",
]
FEES = ["compliance bond", "verification fee", "settlement fine", "clearance fee", "penalty", "security deposit", "legal processing fee", "immigration bond"]
SECRECY = [
    "Do not tell your university or anyone else, this is a confidential federal investigation.",
    "Do not contact your school's international office, they cannot help you with this.",
    "This matter is strictly confidential. If you tell anyone, the case will be escalated.",
    "Stay on the line and do not hang up until the process is complete.",
    "Do not discuss this with your family or your DSO.",
    "Keep this confidential, speaking to others will be treated as obstruction.",
    "",
    "",
]
URGENCY = ["today", "within 2 hours", "immediately", "within the next 60 minutes", "before 5 PM today", "right now", "by end of day", "within 24 hours"]
FAKE_DOMAINS = [
    "sevis-verify-dhs.com", "uscis-case-update.online", "ice-gov-compliance.net", "dhs-sevp-portal.com",
    "studyinthestates-verify.site", "uscis.gov.case-check.info", "sevpportal-verify.co", "f1-status-check.org",
    "immigration-clearance-us.com", "uscis-gov.help", "dhs-gov.org", "sevis-update.us", "icegov-verify.live",
    "bit.ly/3sEv1s", "tinyurl.com/uscis-verify", "uscls.gov-portal.com", "travel-state-visa.info",
]
PII = ["your passport number", "your SSN", "your I-94 number", "your bank login", "a photo of your passport and I-20", "your date of birth and SSN", "your SEVIS ID and passport number"]
SPOOF_NUMBERS = ["(212) 436-9315", "(202) 732-3000", "(800) 375-5283", "(866) 347-2423", "(617) 555-0198", "(408) 555-0122", "+1 202 555 0143"]

COMPANIES_FAKE = ["Nexora Tech Solutions", "BlueOak IT Services", "Primeleaf Consulting", "Vantrix Global", "CloudSpan Systems LLC", "Optimus Data Labs", "Zentra Software", "InfoBridge Staffing", "SkyCore Analytics", "Quantis Tech"]
FREEMAILS = ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "protonmail.com"]
COMPANIES_REAL = [("Microsoft", "microsoft.com"), ("Amazon", "amazon.com"), ("Deloitte", "deloitte.com"), ("Wayfair", "wayfair.com"), ("HubSpot", "hubspot.com"), ("Moderna", "modernatx.com"), ("Fidelity", "fidelity.com"), ("Bose", "bose.com"), ("Liberty Mutual", "libertymutual.com"), ("Akamai", "akamai.com")]
ROLES = ["Data Analyst", "Software Engineer", "Business Analyst", "QA Engineer", "Machine Learning Engineer", "Financial Analyst", "Research Assistant", "Supply Chain Analyst", "Product Analyst"]


def money(r: random.Random, lo=300, hi=5000) -> str:
    v = r.randrange(lo, hi, 50)
    return f"${v:,}"


def pick(r, xs):
    return r.choice(xs)


def maybe(r, p, s):
    return s if r.random() < p else ""


def noise(r: random.Random, text: str) -> str:
    """Light, realistic noise: casing, dropped punctuation, typos, emoji."""
    if r.random() < 0.15:
        text = text.lower()
    if r.random() < 0.15:
        text = text.replace(", ", " ").replace(". ", " ")
    if r.random() < 0.12:
        words = text.split()
        for _ in range(r.randint(1, 3)):
            i = r.randrange(len(words))
            w = words[i]
            if len(w) > 4:
                j = r.randrange(1, len(w) - 1)
                words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2 :]
        text = " ".join(words)
    if r.random() < 0.08:
        text += " " + r.choice(["🙏", "⚠️", "‼️", "👍", "😊"])
    return " ".join(text.split()) if "\n" not in text else text


def agency(r):
    name, short = pick(r, AGENCIES)
    return name.format(city=pick(r, CITIES)), short


def person(r):
    return f"{pick(r, TITLES)} {pick(r, FIRST)} {pick(r, LAST)}"


# --------------------------------------------------------------------------- scams: government impersonation
def gov_call(r):
    a, _ = agency(r)
    parts = [
        pick(r, ["Hello, this is", "Good afternoon, I am", "This is", "Hi, my name is"]) + f" {person(r)} from {a}" + maybe(r, 0.5, f", badge number {r.randint(1000, 9999)}") + ".",
        f"{pick(r, ['I am calling because', 'We are contacting you because', 'Our records show that', 'This is regarding a case where'])} {pick(r, PROBLEMS)}.",
        f"If this is not resolved {pick(r, URGENCY)}, {pick(r, THREATS)}.",
    ]
    if r.random() < 0.8:
        parts.append(f"To {pick(r, ['stop the process', 'clear your record', 'avoid arrest', 'keep your status active', 'verify you are not involved'])} you must pay a {pick(r, FEES)} of {money(r)} using {pick(r, PAYMENTS)}.")
    if r.random() < 0.45:
        parts.append(f"I also need you to confirm {pick(r, PII)} to verify your identity.")
    s = pick(r, SECRECY)
    if s:
        parts.append(s)
    if r.random() < 0.4:
        parts.append(f"If we get disconnected call me back at {pick(r, SPOOF_NUMBERS)}.")
    prefix = pick(r, ["Call transcript: ", "Voicemail: ", "Phone call: ", "", "They said: "])
    return prefix + " ".join(parts), "call_transcript"


def gov_robocall(r):
    a, _ = agency(r)
    return (
        f"{pick(r, ['This is an automated message from', 'Important notice from', 'Final notice from'])} {a}. "
        f"{pick(r, PROBLEMS).capitalize()}. {pick(r, ['Press 1 to speak with an officer', 'Press 1 now to avoid legal action', 'Call back immediately at ' + pick(r, SPOOF_NUMBERS)])}. "
        f"{maybe(r, 0.6, 'Failure to respond ' + pick(r, URGENCY) + ' means ' + pick(r, THREATS) + '.')}"
    ).strip(), "call_transcript"


def gov_sms(r):
    a, short = agency(r)
    dom = pick(r, FAKE_DOMAINS)
    body = pick(r, [
        f"{short} ALERT: {pick(r, PROBLEMS)}. Verify {pick(r, URGENCY)} at {dom} or {pick(r, THREATS)}.",
        f"[{short}] Your F-1 status requires urgent verification. Case #{r.randint(100000, 999999)}. Complete at https://{dom} {pick(r, URGENCY)}.",
        f"Notice from {a}: {pick(r, PROBLEMS)}. Pay the {pick(r, FEES)} of {money(r)} at {dom} to avoid {pick(r, ['deportation', 'arrest', 'visa cancellation', 'SEVIS termination'])}.",
        f"{short}: Dear student, {pick(r, PROBLEMS)}. Reply with {pick(r, PII)} to keep your status active.",
        f"SEVIS NOTICE: your record will be terminated {pick(r, URGENCY)}. Update your info at {dom}. {maybe(r, 0.5, 'Do not ignore this message.')}",
    ])
    return body, "sms"


def gov_email(r):
    a, short = agency(r)
    dom = pick(r, FAKE_DOMAINS)
    sender_dom = pick(r, [dom.split("/")[0], pick(r, FREEMAILS), "dhs-gov.org", "uscis-notice.com", "sevp-mail.net"])
    name = pick(r, STUDENT)
    subj = pick(r, ["URGENT: SEVIS Termination Notice", "Final Warning - Immigration Status Violation", "Action Required: F-1 Status Verification", "Notice of Removal Proceedings", "SEVP Portal Account Suspended", "OPT/EAD Revocation Notice"])
    body = [
        f"Dear {name},",
        f"This is an official notice from {a}. {pick(r, PROBLEMS).capitalize()}.",
        f"You are required to {pick(r, ['verify your identity', 'pay the outstanding ' + pick(r, FEES) + ' of ' + money(r), 'submit ' + pick(r, PII), 'log in and update your records'])} {pick(r, URGENCY)} at https://{dom}.",
        f"Failure to comply will result in the following: {pick(r, THREATS)}.",
        maybe(r, 0.4, pick(r, SECRECY)),
        f"Sincerely,\n{person(r)}\n{a}",
    ]
    return f"From: {short} Compliance <{pick(r, ['notice', 'compliance', 'officer', 'sevis', 'no-reply'])}@{sender_dom}>\nSubject: {subj}\n\n" + "\n".join(b for b in body if b), "email"


def gov_portal_phish(r):
    dom = pick(r, FAKE_DOMAINS)
    return pick(r, [
        f"Your SEVP Portal account will be deactivated in 24 hours due to missing employer information. Log in at https://{dom} to keep your OPT valid.",
        f"Study in the States: we detected a problem with your SEVIS record. Sign in with your passport number to review: {dom}",
        f"USCIS Case Status: your EAD card delivery failed. Pay a {money(r, 20, 120)} redelivery fee at {dom} within 12 hours.",
        f"Your I-20 has been invalidated by DHS. Download the corrected form and confirm your details at https://{dom}/i20",
    ]), "sms"


GOV_GENERATORS = [gov_call, gov_call, gov_robocall, gov_sms, gov_sms, gov_email, gov_email, gov_portal_phish]

# --------------------------------------------------------------------------- scams: OPT / employer fraud
def opt_offer(r):
    comp = pick(r, COMPANIES_FAKE)
    fee = money(r, 200, 3000)
    hook = pick(r, [
        "so your OPT unemployment days stop counting",
        "and we will report you as employed in the SEVP Portal",
        "with guaranteed E-Verify so your STEM OPT extension is approved",
        "even if you don't have a job yet",
        "so you can stay in status after graduation",
    ])
    ask = pick(r, [
        f"There is a one-time onboarding fee of {fee}",
        f"We charge {fee} for the employer letter and I-983 training plan",
        f"You pay {fee} per month and we keep you on our payroll for OPT reporting",
        f"Training and placement program costs {fee}, refundable after you are placed",
        f"E-Verify processing and sponsorship charge is {fee}",
    ])
    pay = pick(r, ["via Zelle", "by wire transfer", "through Cash App", "in USDT", "to our HR account", "by PayPal friends and family"])
    sender = f"{pick(r, ['hr', 'careers', 'opt.team', 'recruit', 'talent'])}.{comp.split()[0].lower()}@{pick(r, FREEMAILS)}"
    channel = pick(r, ["email", "whatsapp", "sms", "linkedin"])
    body = (
        f"{pick(r, ['Hi', 'Hello', 'Dear candidate', 'Greetings'])}, {pick(r, ['we found your profile in an OPT students group', 'your resume was shortlisted', 'we help international students on OPT', 'saw your post about needing an OPT job'])}. "
        f"{comp} can provide an {pick(r, ['OPT employment offer letter', 'offer letter and I-983', 'E-Verify employer letter', 'OPT job confirmation'])} {pick(r, ['within 24 hours', 'today', 'this week'])} {hook}. "
        f"{pick(r, ['Remote role, no interview needed.', 'No real work required.', 'Part-time, flexible hours.', 'Position: ' + pick(r, ROLES) + ', 100% remote.'])} "
        f"{ask} {pay}. {pick(r, ['Only 3 spots left, reply today.', 'Offer valid for 48 hours.', 'Many students already joined.', 'Do not share this offer with your DSO, they make the process slow.', ''])}"
    )
    if channel == "email":
        return f"From: {comp} HR <{sender}>\nSubject: {pick(r, ['OPT Employment Offer', 'Your OPT Job Confirmation', 'STEM OPT Opportunity', 'Offer Letter - Start Immediately'])}\n\n{body}", "email"
    if channel == "whatsapp":
        return body + f" Message me on {pick(r, ['WhatsApp', 'Telegram'])} for details.", "whatsapp"
    return body, channel if channel != "linkedin" else "email"


def opt_threat(r):
    return pick(r, [
        f"Your OPT unemployment days are almost over ({r.randint(80, 89)} of 90 used). Our company can add you as an employee for {money(r, 300, 1500)} so you don't lose status. DM me today.",
        f"STEM OPT holders: your employer was flagged in the ICE OPT fraud investigation. Pay a {money(r, 500, 3000)} employer transfer fee to move to our verified E-Verify company before your status is terminated.",
        f"This is the OPT compliance desk. Your employer did not file your I-983. Send {money(r, 200, 900)} via Zelle to {pick(r, COMPANIES_FAKE)} and we will file it today.",
        f"We sell verified OPT experience letters and pay stubs for H-1B and STEM OPT. {money(r, 150, 800)} per letter, fast delivery, contact on Telegram.",
        f"Unpaid OPT internship available! Pay {money(r, 300, 1200)} training fee and we sign your I-983 and report hours to SEVP. No work needed.",
    ]), pick(r, ["sms", "whatsapp", "email"])


OPT_GENERATORS = [opt_offer, opt_offer, opt_offer, opt_threat]

# --------------------------------------------------------------------------- scams: fake job / task (supplements EMSCAD)
def job_task(r):
    comp = pick(r, [c for c, _ in COMPANIES_REAL] + ["TikTok Shop", "Booking.com", "Shopify Partners"])
    return pick(r, [
        f"Hi, I'm {pick(r, FIRST)} from {comp} recruitment. Part-time remote job: rate products and boost app reviews from your phone, earn {money(r, 100, 500)} per day, no experience needed. To unlock tasks you top up your work account with USDT, commission returned with your deposit. Add me on WhatsApp.",
        f"Hello! We are hiring online assistants to like videos and optimize orders. {money(r, 50, 300)}/day guaranteed. You need to deposit {money(r, 50, 400)} to activate level 1 tasks. Contact on Telegram @{pick(r, FIRST).lower()}_hr{r.randint(1, 99)}.",
        f"Professor {pick(r, LAST)} is looking for a remote research assistant, {money(r, 300, 600)} per week, 5 hours. Please reply from your personal email. You will receive a check to buy equipment from our vendor and send the remaining balance back.",
        f"Congratulations, you have been selected for the {pick(r, ROLES)} position at {comp}, no interview required. Please deposit the attached check of {money(r, 1500, 4000)} with mobile deposit and send {money(r, 900, 1400)} to our equipment vendor via Zelle.",
        f"Personal assistant needed for a busy executive, {money(r, 400, 800)} weekly. Tasks include running errands and buying gift cards for clients. Reply with your full name, address and phone number.",
        f"Remote package inspector job: receive packages at home, relabel and reship them. {money(r, 2000, 3500)}/month. Start today, no interview. Send a copy of your ID and SSN for payroll.",
    ]), pick(r, ["sms", "whatsapp", "email"])


# --------------------------------------------------------------------------- scams: other (housing, tuition, scholarship, toll, parcel)
def other_scam(r):
    return pick(r, [
        f"Room available near {pick(r, SCHOOLS)}, {money(r, 600, 1200)}/month utilities included. I'm currently abroad so I can't show it, send the first month and deposit via Zelle and I will mail you the keys.",
        f"{pick(r, SCHOOLS).replace('your school', 'Student Accounts')}: you have an unpaid tuition balance of {money(r, 400, 3000)}. Pay at {pick(r, ['tuition-portal-pay.com', 'student-billing-help.net', 'bit.ly/tuitpay'])} within 24 hours or your enrollment and I-20 will be cancelled.",
        f"Congratulations! You qualified for the International Student Excellence Scholarship of {money(r, 2000, 10000)}. Pay a {money(r, 50, 200)} processing fee to release the funds.",
        f"EZ-Pass: You have an unpaid toll of $6.{r.randint(10, 99)}. Pay by today to avoid a late fee and license suspension: {pick(r, ['ezpass-tolls-pay.com', 'tollservices-us.info', 'e-zpass.toll-pay.xyz'])}",
        f"USPS: your package is on hold due to an incomplete address. Update within 12 hours: {pick(r, ['usps-redelivery.top', 'usps.post-track.info', 'tinyurl.com/uspsfix'])}",
        f"Chase Fraud Alert: a payment of {money(r, 300, 1500)} was attempted. If this wasn't you, verify your account at {pick(r, ['chase-secure-verify.com', 'chaseonline.account-help.net'])} and enter your login and card number.",
        f"Student loan forgiveness for international students! Apply now, a {money(r, 100, 500)} application fee is required. Limited time offer.",
    ]), pick(r, ["sms", "email", "whatsapp"])


# --------------------------------------------------------------------------- legitimate hard negatives
def legit_dso(r):
    school = pick(r, ["International Student and Scholar Services", "Office of Global Services", "International Student Office", "Office of International Affairs", "ISSS"])
    dom = pick(r, ["university.edu", "stateu.edu", "northbridge.edu", "lakeside.edu", "wit.edu", "cityu.edu"])
    body = pick(r, [
        f"F-1 students must report a change of U.S. address within 10 days. Please log in to the student portal and submit the Address Update e-form. We will update your SEVIS record.",
        f"Reminder for students on post-completion OPT: you must report your employer name and address within 10 days of starting a job, using the SEVP Portal. If you have questions, attend virtual drop-in advising.",
        f"If you plan to travel during winter break, make sure your I-20 has a valid travel signature from a DSO, signed within the past 12 months. Request a signature through the portal at least 5 business days before travel.",
        f"STEM OPT students: your 12-month self-evaluation on Form I-983 is due soon. Complete it with your supervisor and submit it to our office through the portal. Contact your advisor if your employer information changed.",
        f"Your OPT application review is complete. Your updated I-20 with the OPT recommendation is ready in the portal. Please file Form I-765 with USCIS within 30 days of the DSO recommendation date.",
        f"Students on OPT: you are allowed a limited number of unemployment days. Please review the OPT unemployment rules on our website and contact an advisor if you are close to the limit. Do not pay anyone who offers to 'fix' your unemployment days.",
        f"SCAM WARNING: Students have reported calls from people claiming to be ICE or police officers, demanding payment to avoid deportation. Government agencies will not call you to demand money or gift cards. Hang up and contact our office directly.",
        f"Fraud alert: We have received reports of fake job offers sent to student emails promising easy remote work. Do not deposit checks or send money to 'employers'. Report suspicious emails to the IT security team.",
        f"Your SEVIS registration for the fall semester is complete. No further action is needed. If you change your course load, talk to your advisor before dropping below full-time.",
        f"Orientation for new international students is on Monday. Please bring your passport, I-20 and I-94 printout to check-in so we can complete your SEVIS registration.",
    ])
    return f"From: {school} <{pick(r, ['isss', 'ogs', 'intl', 'globalservices', 'iso'])}@{dom}>\nSubject: {pick(r, ['Reminder', 'Important: action needed', 'Weekly update', 'OPT reporting reminder', 'Scam alert', 'Travel signatures', 'Information'])}\n\n{body}", "email"


def legit_uscis(r):
    rec = f"IOE{r.randint(10**9, 10**10 - 1)}"
    return pick(r, [
        f"USCIS Case Status: The status of your case, receipt number {rec}, has been updated. Log in to your USCIS online account at my.uscis.gov to view it. USCIS will never ask for payment by phone.",
        f"From: USCIS <noreply@uscis.dhs.gov>\nSubject: Case Status Update\n\nThe status for receipt number {rec} has changed to Card Was Mailed To Me. Visit uscis.gov/casestatus for details.",
        f"USCIS: We received your Form I-765 and mailed you a receipt notice. Your receipt number is {rec}. Track your case at egov.uscis.gov.",
        f"Your biometrics appointment notice has been mailed. Please bring the notice and a photo ID to the Application Support Center on the scheduled date. Check the notice for the address.",
    ]), pick(r, ["sms", "email"])


def legit_recruiter(r):
    comp, dom = pick(r, COMPANIES_REAL)
    role = pick(r, ROLES)
    name = f"{pick(r, FIRST)} {pick(r, LAST)}"
    return pick(r, [
        f"From: {name} <{name.split()[0].lower()}@{dom}>\nSubject: Interview invitation - {role}\n\nHi {pick(r, STUDENT)}, thank you for applying to the {role} role at {comp}. We'd like to schedule a 30-minute video interview next week. Please pick a time through the scheduling link in your candidate portal. Let me know if you need any accommodations.",
        f"From: {comp} Careers <careers@{dom}>\nSubject: Your application\n\nThank you for applying. Your application for {role} is under review. You can check status anytime in our careers portal. We never ask candidates for payment at any stage of hiring.",
        f"Hi {pick(r, STUDENT)}, I'm a recruiter at {comp}. Your profile matches our {role} opening. Would you be open to a quick call this week? You can also apply directly on {dom}/careers. Happy to answer questions about sponsorship and STEM OPT.",
        f"From: HR <hr@{dom}>\nSubject: First day - I-9 documents\n\nWelcome to {comp}! On your first day, please bring original documents for Form I-9, such as your passport, I-94 and EAD card. HR will verify them in person and complete E-Verify. Please don't email copies of these documents.",
    ]), "email"


def legit_bank_misc(r):
    return pick(r, [
        f"Bank of America: Did you attempt a purchase of {money(r, 20, 400)} at an online store? Reply YES or NO. We will never ask for your PIN or password by text. If unsure, call the number on the back of your card.",
        f"Your package is out for delivery today. Track it in the app.",
        f"University IT: Scheduled maintenance this Saturday 2-4 AM. Email and the student portal may be unavailable. No action is needed.",
        f"Hi {pick(r, STUDENT)}, your lease renewal for apartment 4B is ready to sign in the resident portal. Rent and deposit are paid only through the portal. Stop by the leasing office if you have questions.",
        f"Student Accounts: Your fall tuition statement is now available in the student portal. Payment is due by the date shown. Please pay only through the official portal.",
        f"Reminder: Your appointment with the Career Center is tomorrow at 2 PM. Bring a printed copy of your resume.",
        f"Hey it's {pick(r, FIRST)} from the lab, the group meeting moved to Thursday 3pm, see you there!",
        f"IRS reminder for nonresident students: you may need to file Form 8843 even if you had no income. Your school's tax software access code is available on the international office website.",
        f"Mom: did you reach the dorm? call me when you're free, we're worried",
        f"The Social Security office reminder: bring your passport, I-94 and a letter from your employer or DSO when applying for an SSN in person.",
    ]), pick(r, ["sms", "email"])


GENERATORS = {
    "gov_impersonation": GOV_GENERATORS,
    "opt_employer_fraud": OPT_GENERATORS,
    "fake_job_task": [job_task],
    "other_scam": [other_scam],
    "legitimate": [legit_dso, legit_dso, legit_dso, legit_uscis, legit_recruiter, legit_recruiter, legit_bank_misc],
}


def generate(n_per_class: dict[str, int], seed: int) -> list[dict]:
    r = random.Random(seed)
    rows, seen = [], set()
    for label, n in n_per_class.items():
        tries = 0
        count = 0
        while count < n and tries < n * 20:
            tries += 1
            text, channel = pick(r, GENERATORS[label])(r)
            text = noise(r, text)
            if text in seen:
                continue
            seen.add(text)
            rows.append({"text": text, "label": label, "channel": channel, "source": "synthetic"})
            count += 1
    r.shuffle(rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--gov", type=int, default=900)
    ap.add_argument("--opt", type=int, default=700)
    ap.add_argument("--job", type=int, default=300)
    ap.add_argument("--other", type=int, default=300)
    ap.add_argument("--legit", type=int, default=1100)
    args = ap.parse_args()
    rows = generate({"gov_impersonation": args.gov, "opt_employer_fraud": args.opt, "fake_job_task": args.job, "other_scam": args.other, "legitimate": args.legit}, args.seed)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    from collections import Counter

    print(f"wrote {len(rows)} rows to {OUT}: {Counter(r['label'] for r in rows)}")


if __name__ == "__main__":
    main()
