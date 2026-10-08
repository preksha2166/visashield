"""Source for data/eval/real_world_dev.jsonl: real-world DEVELOPMENT set (never trained on;
used for error analysis while building signals). The final, independently written
held-out set is data/eval/real_world_test.jsonl.

Scam examples are reconstructions of scams described in published 2024-2026 alerts
(university international offices, DHS, FTC, ICE, IC3), rewritten in new wording and
deliberately varied in style so they differ from the synthetic training templates.
Legitimate examples are hard negatives: genuine-style messages that also sound urgent.
Contact details are fictional unless an alert published them as spoofed numbers.

Usage: python -m training.real_world_src   (writes data/eval/real_world_dev.jsonl)
"""
import json

from app import config

CU_AR11 = "https://www.colorado.edu/isss/2026/06/01/scam-alert-uscis-ar-11-phone-call-and-email"
CU_ICE = "https://www.colorado.edu/isss/2026/06/01/scam-alert-spoofed-calls-ice-and-boulder-police-department"
CU_FEE = "https://www.colorado.edu/isss/2024/10/18/scam-alert-unpaid-cu-boulder-fees-phone-scam"
CU_OPT = "https://www.colorado.edu/isss/2025/05/27/optional-practical-training-opt-and-unemployment"
WAYNE = "https://oip.wayne.edu/news/scam-emails-and-calls-target-international-students-and-scholars-66119"
SJSU = "https://sjsu.edu/isss/resources/scam-alerts.php"
UW = "https://iss.washington.edu/alert-new-scam-targets-international-students/"
DHS26 = "https://studyinthestates.dhs.gov/2026/02/beware-of-dhs-imposters-protecting-foreign-students-from-scams"
JHU = "https://ois.jhu.edu/ice-scam-targeting-international-students"
SEVP_BCM = "https://www.ice.gov/doclib/sevis/pdf/bcm260302.pdf"
ICE_FINDREAM = "https://www.ice.gov/news/releases/chinese-businesswoman-indicted-student-visa-work-visa-fraud-charges"
FTC_JOBS = "https://consumer.ftc.gov/articles/job-scams"
FTC_GOV = "https://consumer.ftc.gov/articles/how-avoid-government-impersonation-scam"
FTC_RENT = "https://consumer.ftc.gov/articles/rental-listing-scams"
IC3_PSA = "https://www.ic3.gov/PSA/2025/PSA250513"
USCIS_SCAMS = "https://www.uscis.gov/scams-fraud-and-misconduct/avoid-scams/common-scams"
PORTAL = "https://studyinthestates.dhs.gov/sevis-help-hub/student-records/fm-student-employment/sevis-and-the-sevp-portal/portal-email-notices"
STEM = "https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt"
HAND = "handwritten"

E = []


def add(label, channel, src, note, text):
    E.append({"text": text.strip(), "label": label, "channel": channel, "source_url": src, "note": note})


G = "gov_impersonation"
# ---------------------------------------------------------------- government impersonation (18)
add(G, "call_transcript", CU_AR11, "adapted from CU Boulder AR-11 alert",
    "Caller ID showed USCIS. The man said I never filed my AR-11 change of address so I am out of status and immigration can remove me today. He wanted me to text pictures of my passport, visa and I-20 and also my bank name and SSN so they could 'update the file'. Every time I said I wanted to call my school he said if I hang up the case goes to the judge automatically.")
add(G, "email", CU_AR11, "adapted from CU Boulder AR-11 alert (gmail follow-up)",
    "From: USCIS Field Office Compliance <uscis.fieldoffice.compliance@gmail.com>\nSubject: AR-11 Non-Compliance - Case Escalated\n\nThis is a follow up to our call. Our records indicate Form AR-11 was not received for your current address. Per federal regulation, non-compliant nonimmigrants are subject to removal. Reply to this email with a scanned copy of your passport biographic page, your Social Security card and a recent bank statement within 3 hours to stop escalation.")
add(G, "call_transcript", CU_ICE, "adapted from CU Boulder spoofed ICE call alert",
    "Got a call from (212) 436-9315 which google says is ICE New York. Guy said he was Agent Mark Tillman, gave me some badge number, said there is an error in my I-94 record and a warrant has been issued and I'll be put in removal proceedings unless it's corrected today. He asked which bank I use and how much money is in my account.")
add(G, "call_transcript", CU_ICE, "adapted from CU Boulder alert (second call spoofing local police)",
    "Second call came maybe 20 mins later from what looked like the police non-emergency number. A woman said she was a sergeant and that ICE had forwarded my warrant and officers would come to my apartment tonight unless I settled with the federal agent who called earlier. She told me not to leave my apartment and not to call anyone.")
add(G, "call_transcript", WAYNE, "adapted from Wayne State OIP CBP/ICE gift card case",
    "They said they're from Customs and Border Protection and I didn't report my change of address so I could go to prison and be deported. Then another man from ICE got on and said they'd freeze my bank accounts. They told me to go to Walgreens and buy $500 in Apple gift cards and read the numbers. After I did, they said I needed another $1000 for the 'second verification'.")
add(G, "call_transcript", SJSU, "adapted from SJSU scam catalog (SSA impersonation)",
    "Recorded message: This is the Social Security Administration. Your social security number has been suspended because it was used in criminal activity in Texas. To avoid legal action and arrest, press 1 now to speak with an officer.")
add(G, "call_transcript", SJSU, "adapted from SJSU catalog (DHS spoofed, eBay gift cards)",
    "dhs officer called, number showed as a real Homeland Security number. said i owe a fine for incorrect documents on my visa application, $2,300, and that it has to be paid in ebay or apple gift cards because it's an expedited federal settlement. said my sevis is terminated until paid")
add(G, "call_transcript", SJSU, "adapted from SJSU catalog (consulate impersonation)",
    "Automated voice in Mandarin then English: This is the Chinese Consulate General. You have an important document waiting for pickup. Press 9 for details. Then a person said a package with fake passports under my name was intercepted and transferred me to a 'Shanghai police officer' on video call who showed a warrant and said I must transfer my savings to a supervised account to prove innocence and keep it secret.")
add(G, "sms", DHS26, "adapted from DHS Feb 2026 advisory tactics (fix status for a fee)",
    "DHS NOTICE: A problem was found in your SEVIS record (Ref SV-88213). An approved agent can correct your record before termination for a one-time $850 service fee. Reply YES to receive payment instructions. Do not contact your school, they cannot access federal files.")
add(G, "email", DHS26, "adapted from DHS advisory (A-number / I-94 requests, crypto)",
    "From: Homeland Security Investigations <hsi-casework@dhs-gov.support>\nSubject: Identity verification required - Case HSI-2026-0419\n\nDear Student,\nYour Alien Registration Number and I-94 admission record are linked to an open investigation. Provide both numbers and a selfie holding your passport. A refundable security deposit of $1,200 in USDT is required while the investigation is open. Wallet address will be shared after verification.")
add(G, "call_transcript", JHU, "adapted from JHU OIS ICE scam alert",
    "Person said she was from ICE and that my visa had been flagged and I'd be detained at my next entry to the US unless I paid to clear the flag. She asked me to stay on the line while she 'connected the legal department'. She knew my full name and school.")
add(G, "sms", CU_FEE, "adapted from CU Boulder unpaid-fee call alert",
    "University Bursar: international student fee unpaid. Immigration will be notified and deportation will begin today. Send passport no. and visa no. to confirm identity, then pay $680 by Zelle to bursar.payments@outlook.com.")
add(G, "email", UW, "adapted from UW fake academic integrity dept alert",
    "From: Academic Integrity Department <integrity.office.dept@protonmail.com>\nSubject: Notice of Academic Misconduct - Visa Implications\n\nOur department has received a report of plagiarism in your coursework. As an F-1 student, a confirmed violation will be reported to SEVIS and may result in termination of your status. To resolve this privately, reply within 24 hours with your student ID, date of birth and passport number.")
add(G, "email", SJSU, "adapted from SJSU (fake USCIS email from odd domain)",
    "From: USCIS Online <alerts@uscis-services.link>\nSubject: Your case requires action\n\nWe were unable to verify the biometrics associated with your EAD application. Please click the link below and sign in with your bank account to confirm your identity and pay the $85 re-verification fee: http://uscis-services.link/verify")
add(G, "whatsapp", FTC_GOV, "adapted from FTC government imposter guidance",
    "Hello this is Inspector Williams, US Immigration. We tried calling you. Your case number IMM-7731 is now active. Respond on this WhatsApp only. You must clear the penalty via Bitcoin ATM today, I will guide you to the nearest machine. Don't discuss with others, this is a sealed case.")
add(G, "call_transcript", IC3_PSA, "adapted from IC3 2025 PSA on official impersonation",
    "Voicemail: Hi, this is Special Agent Robert Kline with the FBI. Your identity was used in a federal fraud case and your immigration status is under review. Call me back urgently at 202-555-0177 so we can verify you're a victim and not a suspect, otherwise a warrant will be issued.")
add(G, "sms", DHS26, "adapted from DHS advisory (SEVP portal phishing style)",
    "SEVP Portal: your account is locked due to missing employer info. Unlock now or your OPT ends in 24h -> sevp-portal-login.com/unlock")
add(G, "call_transcript", USCIS_SCAMS, "adapted from USCIS common scams (payment)",
    "a man said he was a USCIS officer and that my OPT approval was on hold because of a fee error and he could fix it over the phone if I paid $430 through Western Union right now, otherwise I'd lose my EAD.")

O = "opt_employer_fraud"
# ---------------------------------------------------------------- OPT / employer fraud (10)
add(O, "whatsapp", ICE_FINDREAM, "adapted from ICE Findream/Sinocontech case (paid proof of employment)",
    "OPT/H1B employer service available. We are a registered US LLC. You pay monthly, we issue offer letter, employment verification letter and paystubs so your OPT stays active. No need to actually work. Fast, safe, many students use us. Join our WeChat group for price list.")
add(O, "email", SEVP_BCM, "adapted from SEVP BCM 2603-02 STEM OPT employer fraud red flags",
    "Subject: STEM OPT Position - Remote (Bench)\n\nHi, we are an IT consulting and staffing firm. We can sign your I-983 and E-Verify you within 2 days. You will be on our bench until we find a client project, so no salary during bench period. Bench and marketing fee is $1,500 for 3 months. Our office address can be used as your worksite on the I-983. Communication through WeChat only.")
add(O, "sms", CU_OPT, "adapted from CU Boulder OPT unemployment article (scam that exploits it)",
    "Running out of OPT unemployment days? Don't panic. We add you as volunteer research associate today and report it to SEVP so the clock stops. $399/month, cancel anytime. Text START.")
add(O, "email", SEVP_BCM, "adapted from SEVP red flags (vague firm, mass hiring)",
    "From: Talent Desk <talentdesk.opthire@gmail.com>\nSubject: Congrats! Selected for Data Analyst (OPT)\n\nYou and 14 other students from your university are selected for our Data Analyst internship. No interview needed. To finalize onboarding please pay a $250 background check & training fee, after which we will send your offer letter for SEVP portal reporting.")
add(O, "whatsapp", SEVP_BCM, "adapted from SEVP BCM (remote via apps, staffing agency)",
    "hi bro, our company can put you on STEM OPT, real E-Verify number. you just pay your own salary to us monthly and we pay it back as payroll so it shows on W-2. many guys doing this. dm me")
add(O, "email", ICE_FINDREAM, "adapted from ICE fake-employer cases",
    "Subject: Experience letter + I-983 package\n\nWe provide genuine-looking experience letters on company letterhead, signed I-983 training plans and HR verification by phone for STEM OPT applications. Package price $700. 100% approval rate, refund if rejected. Payment by Zelle or crypto.")
add(O, "linkedin", FTC_JOBS, "adapted from FTC job scam guidance + OPT context",
    "Hi! Saw you're on OPT and looking. We are hiring Java developers, guaranteed placement with Fortune 500 clients in 30 days. Our 6 week training program costs $3,000 which is deducted from your future salary, but we need $1,000 upfront today to reserve your seat and process your E-Verify.")
add(O, "sms", CU_OPT, "adapted from SEVP unemployment context (fake SEVP threat + fee)",
    "SEVP ALERT: You have exceeded 90 days of OPT unemployment. Your SEVIS will be terminated in 24 hours. Pay $200 reinstatement fee at sevp-reinstate.us to keep your status.")
add(O, "email", STEM, "adapted from USCIS STEM OPT rules (E-Verify requirement abused)",
    "Dear candidate, our company is not enrolled in E-Verify yet, but we can use our partner company's E-Verify number for your STEM OPT application. A one-time partner sponsorship fee of $900 applies. Please don't mention the partner company to your DSO, just list our name on the I-983.")
add(O, "whatsapp", SEVP_BCM, "adapted from SEVP site-visit findings (empty worksites)",
    "Offer: Business Analyst, worksite is listed at our Edison NJ office but you work from home in any state, never need to come in. HR and payroll are in our India office. Pay $150 processing to receive the offer letter today.")

J = "fake_job_task"
# ---------------------------------------------------------------- fake job / task (10)
add(J, "email", SJSU, "adapted from SJSU Google Chat fake HR / fake check",
    "Hi, this is Karen from HR at a well-known software company, contacting you via Google Chat. After reviewing your resume we are offering you a remote Junior Data Entry role at $32/hr. No interview or background check needed. We'll mail you a check for $3,850 to buy your home office equipment from our approved vendor. Deposit it and send the vendor payment via Zelle.")
add(J, "whatsapp", FTC_JOBS, "adapted from FTC task scam description",
    "Hello dear, are you interested in a flexible online job? You help merchants increase app ratings by completing 40 'orders' per set. Daily income 150-800 USD. After a few sets your account balance goes negative and you need to recharge with crypto to continue and withdraw your commission.")
add(J, "sms", FTC_JOBS, "adapted from FTC job scams (text recruiter)",
    "Hi, I'm Ashley from a staffing agency, your resume was recommended to us. Remote part-time, 60-90 min/day, $300-$900 per day. Paid daily. Please reply via WhatsApp to learn more.")
add(J, "email", FTC_JOBS, "adapted from FTC fake check scam guidance",
    "Subject: Campus Research Assistant (paid)\n\nHello student, I am Dr. Allen Hughes, a professor in the biology department. I need a part-time assistant for errands while I travel to a conference. $450 weekly. Please reply with your personal (non-school) email and phone number. I will send you a check to purchase supplies for my lab.")
add(J, "telegram", FTC_JOBS, "adapted from FTC task scam / crypto",
    "Welcome to the TikTok merchant team! Today's tasks: like 30 videos = $45. Reach VIP level to unlock high-commission tasks: VIP1 requires a 100 USDT top-up. Our customer service will help you register on the crypto exchange.")
add(J, "email", FTC_JOBS, "adapted from FTC reshipping scam guidance",
    "Position: Quality Control Inspector (work from home). Receive packages, take photos of contents, and reship them using prepaid labels we email you. $2,500/month plus bonus. Please send a copy of your driver's license and SSN for payroll setup.")
add(J, "sms", FTC_JOBS, "adapted from FTC job scams (mystery shopper)",
    "Mystery shopper wanted in your area. Evaluate a money transfer store: you will receive a $1,950 check, keep $300 as pay and send the rest through Western Union and rate the service.")
add(J, "whatsapp", FTC_JOBS, "adapted from FTC job scams (crypto investment job)",
    "Hi I got your number from a job group. We hire students as crypto arbitrage assistants, just follow my signals on the trading app, guaranteed 10% daily profit. Start with at least $200 deposit, you can withdraw anytime.")
add(J, "email", SJSU, "adapted from SJSU (no interview job + equipment)",
    "Congratulations! Following your application on Handshake, the hiring team has approved you for the Virtual Administrative Assistant role. Interview was conducted via text chat. Your start-up kit check will arrive by FedEx tomorrow; please confirm your mailing address and mobile banking app.")
add(J, "sms", FTC_JOBS, "adapted from FTC job scams (training fee)",
    "Amazon Hiring Team: You are pre-approved for a Remote Customer Support job, $25/hr. Complete a $79 certification course to activate your employee ID: amzn-careers-hr.com/activate")

S = "other_scam"
# ---------------------------------------------------------------- other scams (6)
add(S, "email", FTC_RENT, "adapted from FTC rental listing scam guidance",
    "Hi, thanks for your interest in the 1BR near campus, $850/mo. I'm working overseas as a missionary so I can't show the apartment. Send the first month + deposit ($1,700) by Zelle and I will ship the keys by FedEx. Many students are asking so first to pay gets it.")
add(S, "sms", SJSU, "adapted from SJSU catalog (academic integrity payment)",
    "Student Conduct: you have an unresolved academic integrity violation. Pay the $300 resolution fine within 48 hours or face expulsion: student-conduct-pay.com")
add(S, "email", FTC_GOV, "adapted from FTC impersonation guidance (scholarship / grant)",
    "Congratulations! You've been selected for the Federal International Student Grant ($5,000). To release funds, pay the $149 processing fee using a prepaid debit card and send us the card number and PIN.")
add(S, "sms", FTC_GOV, "adapted from FTC 2025 toll-text trend",
    "Toll Services: Your vehicle has an outstanding toll of $4.35. Avoid a $50 late fee and registration hold. Pay now: tolls-us-pay.com/inv8823")
add(S, "sms", FTC_GOV, "adapted from FTC bank impersonation guidance",
    "Wells Fargo: Unusual login detected on your account. If this was not you, verify your identity at wf-secure-alerts.com within 1 hour or your account will be locked.")
add(S, "email", CU_FEE, "adapted from CU Boulder fee scam (tuition)",
    "From: Student Financial Services <sfs.billing.dept@outlook.com>\nSubject: FINAL NOTICE - unpaid tuition\n\nYour spring registration and I-20 will be cancelled today due to an unpaid balance of $1,240. Pay immediately via the secure portal: tuition-balance-pay.net")

L = "legitimate"
# ---------------------------------------------------------------- legitimate hard negatives (18)
add(L, "email", CU_OPT, "genuine-style SEVP unemployment warning (urgent but real, no payment)",
    "From: SEVP Portal <sevp.portal@ice.dhs.gov>\nSubject: Action required: OPT employment information\n\nOur records indicate you have accrued unemployment time on post-completion OPT that may exceed the allowed limit. If your employment information is not updated in the SEVP Portal within 15 days, your SEVIS record may be terminated. If you believe this is an error, log in to the SEVP Portal to report your employment or contact your DSO.")
add(L, "email", PORTAL, "genuine-style SEVP Portal account email",
    "From: SEVP Portal <sevp.portal@ice.dhs.gov>\nSubject: SEVP Portal account created\n\nYour DSO has recommended you for OPT and your EAD has been approved. An SEVP Portal account has been created for you. Use the link in this email to set your password and report your employer information. The SEVP Portal will never ask for payment.")
add(L, "email", HAND, "genuine-style DSO travel signature reminder",
    "From: Office of Global Services <ogs@university.edu>\nSubject: Traveling for winter break? Check your I-20 signature\n\nHi everyone, if you are leaving the US over break, your I-20 needs a travel signature from a DSO dated within the last 12 months. Please request it through the student portal by Dec 5. Late requests may not be processed before you leave. Questions? Join walk-in advising Tue/Thu 1-4pm.")
add(L, "email", HAND, "genuine-style ISSS scam warning (mentions scam vocabulary)",
    "From: International Student and Scholar Services <isss@university.edu>\nSubject: Alert: calls impersonating ICE and USCIS\n\nSeveral students reported calls from people claiming to be ICE agents, saying their SEVIS was terminated and demanding gift cards or Zelle payments to avoid arrest. These calls are scams. Government agencies will never demand payment by phone. If you receive one, hang up, do not share personal information, and contact ISSS. You are not in trouble.")
add(L, "sms", "https://egov.uscis.gov/", "genuine-style USCIS case status text",
    "USCIS: The status of your case IOE0912345678 was updated. Log in to your USCIS online account at my.uscis.gov or check egov.uscis.gov for details.")
add(L, "email", HAND, "genuine-style DSO OPT reporting reminder",
    "From: International Student Office <intl@university.edu>\nSubject: Reminder for OPT students - report your employer within 10 days\n\nCongratulations to everyone who started new jobs! Remember that you must report your employer name, address and start date within 10 days through the SEVP Portal. If you are a STEM OPT student, submit a new I-983 to our office when your employer changes. Contact us if you're unsure what counts as qualifying employment.")
add(L, "email", HAND, "genuine-style employer HR I-9 email (mentions passport, E-Verify)",
    "From: People Team <onboarding@hubspot.com>\nSubject: Your first day - I-9 verification\n\nWelcome aboard! On your first day, please bring original documents for Form I-9 - for F-1 OPT employees this is usually your passport, I-94 and EAD card. We'll verify them in person and complete E-Verify. Please don't email copies of your documents. Payroll setup happens in Workday after day one.")
add(L, "email", HAND, "genuine-style recruiter outreach on company domain",
    "From: Priya Raman <praman@akamai.com>\nSubject: Software Engineer I - interview availability\n\nHi Minh, thanks for applying to the Software Engineer I role in Cambridge. We'd like to set up a 45-minute technical phone screen. Please choose a slot through the scheduling link in your candidate portal. We do sponsor STEM OPT for this role. Let me know if you need any accommodations.")
add(L, "sms", HAND, "genuine-style bank fraud alert (no link, call card number)",
    "Chase: Did you make a $412.99 purchase at BESTBUY.COM? Reply Y or N. To speak to us, call the number on the back of your card. We'll never ask for your password or one-time code.")
add(L, "email", HAND, "genuine-style DSO address update requirement",
    "From: ISSS <isss@stateu.edu>\nSubject: Moved recently? Update your address within 10 days\n\nF-1 students must update their U.S. residential address within 10 days of moving. Submit the change through the MyISSS portal and we'll update SEVIS for you. You don't need to file anything else with USCIS for this.")
add(L, "email", HAND, "genuine-style university IT phishing warning",
    "From: Information Technology Services <its-security@university.edu>\nSubject: Phishing alert: fake job offers sent to student accounts\n\nWe've blocked a wave of emails offering remote assistant jobs that ask students to deposit a check and buy equipment. Delete these messages. Our IT staff will never ask for your password. Forward suspicious emails to phish@university.edu.")
add(L, "whatsapp", HAND, "genuine-style message from a friend about OPT",
    "hey did you get your EAD yet? mine came yesterday, USCIS app updated to card was mailed. btw the ISSS opt workshop is thursday, they explain the unemployment days thing, wanna go together?")
add(L, "email", HAND, "genuine-style tuition statement via official portal",
    "From: Bursar's Office <bursar@university.edu>\nSubject: Spring statement available\n\nYour spring tuition statement is now available in the student portal. Payment is due January 15. Pay only through the student portal or by the methods listed on the Bursar website. If you have a hold, your advisor can explain how to resolve it.")
add(L, "email", "https://www.irs.gov/individuals/international-taxpayers/taxation-of-nonresident-aliens", "genuine-style school tax reminder",
    "From: International Student Office <intl@university.edu>\nSubject: Tax season for international students\n\nAll F-1 students and their dependents must file Form 8843 each year, even with no income. Students with U.S. income may also need to file a federal return. Access codes for our free nonresident tax software are available in the portal. The IRS will never call you to demand immediate payment.")
add(L, "email", HAND, "genuine-style landlord lease email",
    "Hi Arjun, your lease for unit 3C starting Aug 20 is ready to sign in the resident portal. The security deposit and first month's rent can be paid in the portal by ACH or card, or by check at the leasing office. Feel free to stop by for a tour of the unit before signing.")
add(L, "email", HAND, "genuine-style career center job alert",
    "From: Career Center <careers@university.edu>\nSubject: New on Handshake: 12 STEM OPT-friendly roles\n\nWe've curated new postings from employers who have hired our international alumni. Always apply through official company career pages and never pay a fee for an application, training or an offer letter. Book a resume review with an advisor this week.")
add(L, "call_transcript", HAND, "genuine-style DSO phone call (school calls, no payment)",
    "Hi, this is Jenna from the international student office returning your call about your reduced course load request. Your RCL was approved and I've updated your SEVIS record. You'll see the updated I-20 in the portal tomorrow. Let us know if you have questions.")
add(L, "email", "https://www.uscis.gov/forms/filing-guidance/preparing-for-your-biometric-services-appointment", "genuine-style biometrics notice reminder",
    "From: USCIS <uscis-noreply@dhs.gov>\nSubject: Your biometrics appointment\n\nA notice for your biometric services appointment was mailed to your address on file. Bring the appointment notice and a valid photo ID such as your passport to the Application Support Center listed on the notice. Visit uscis.gov to reschedule if needed.")


def main():
    out = config.DATA_DIR / "eval" / "real_world_dev.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for row in E:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    from collections import Counter

    print(f"wrote {len(E)} rows: {dict(Counter(r['label'] for r in E))}")


if __name__ == "__main__":
    main()
