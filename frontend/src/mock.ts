import type { AnalyzeResponse, Situation } from './types'

/**
 * Realistic canned responses for `?mock=1`, so the UI can be demoed and screenshotted
 * before the backend is ready. Phone numbers and domains are fictional.
 */

const GOV_TEXT_REDACTED = `Call transcript (voicemail, caller ID showed "DHS Washington DC"):
"This is Officer James Miller, badge number 4471, from the Department of Homeland Security, Immigration and Customs Enforcement. This call is regarding your SEVIS record. Our system shows discrepancies in your F-1 status and your SEVIS ID [SEVIS_ID] has been flagged for termination. A warrant will be issued for your arrest and deportation within 2 hours unless you resolve this today. Do NOT contact your university or your DSO, this is a confidential federal investigation and telling anyone will make your case worse. To clear the flag you must pay a verification bond of $1,500 using Target or Apple gift cards. Call me back immediately at +1 (202) 555-0147 and stay on the line. You can also verify your case at http://sevis-verify-dhs.com/case."`

const GOV_ACTIONS: Record<Situation, string[]> = {
  not_responded: [
    'Do not call the number back, and do not buy gift cards or send any money.',
    'Block the number. Caller ID can be faked, so a "DHS" or "ICE" name on screen proves nothing.',
    "Contact your school's international student office (DSO) using the phone number on your school's official website, and tell them about this call.",
    'Do not visit sevis-verify-dhs.com or enter any information there.',
    'Report the call at ReportFraud.ftc.gov (you can paste the report text below).',
  ],
  paid: [
    'Stop all contact with the caller. Do not send any more money, even if they promise a refund.',
    'If you paid with gift cards, call the gift card company now (the number on the back of the card) and ask them to freeze the funds. Keep the cards and receipts.',
    'If you paid by bank transfer, Zelle, or card, call your bank immediately and say it was a fraud.',
    'Report the scam at ReportFraud.ftc.gov and IC3.gov. Include how much you paid and how.',
    "Tell your DSO, using the number on your school's official website. Your SEVIS record is not affected by this call.",
  ],
  shared_info: [
    'Stop all contact with the caller and block the number.',
    'If you shared your SSN, place a free credit freeze at Equifax, Experian, and TransUnion.',
    'Get an IRS Identity Protection PIN at IRS.gov to protect your tax refund.',
    'If you shared your passport or I-20 details, tell your DSO using the number on your school\'s official website, and watch for follow-up scam contacts.',
    'Report it at IdentityTheft.gov and ReportFraud.ftc.gov.',
  ],
}

const govImpersonation: AnalyzeResponse = {
  verdict: 'likely_scam',
  risk_score: 0.96,
  category: 'gov_impersonation',
  category_label: 'Government impersonation',
  category_probs: {
    gov_impersonation: 0.91,
    other_scam: 0.04,
    opt_employer_fraud: 0.02,
    fake_job_task: 0.01,
    legitimate: 0.02,
  },
  summary: 'This is very likely a scam pretending to be ICE / DHS.',
  explanation: `The caller claims to be an ICE officer and threatens arrest and deportation within hours unless you pay a "verification bond" in gift cards. US government agencies never ask for payment by gift card, and they do not threaten arrest over the phone.

The caller also tells you not to contact your school. Only your school's DSO can update your SEVIS record, so a real problem with your status would come from your DSO — not from an officer demanding secrecy.

The link uses sevis-verify-dhs.com, which is not a .gov website. Real Department of Homeland Security websites end in .gov.`,
  reasons: [
    {
      signal: 'violates_official_rule:gov_no_giftcard_payment',
      text: 'Demands payment with gift cards. No US government agency accepts gift cards as payment.',
      weight: 0.34,
      source_url: 'https://consumer.ftc.gov/articles/gift-card-scams',
      source_title: 'FTC: Gift card scams',
    },
    {
      signal: 'violates_official_rule:only_dso_updates_sevis',
      text: 'Says your SEVIS record will be "terminated" by a phone officer. Only your school\'s DSO can update SEVIS.',
      weight: 0.22,
      source_url: 'https://studyinthestates.dhs.gov/',
      source_title: 'DHS Study in the States',
    },
    {
      signal: 'gov_claim_non_gov_domain',
      text: 'Claims to be DHS/ICE but sends you to sevis-verify-dhs.com, which is not a .gov website.',
      weight: 0.17,
      source_url: 'https://www.uscis.gov/scams-fraud-and-misconduct',
      source_title: 'USCIS: Scams, fraud and misconduct',
    },
    {
      signal: 'secrecy',
      text: 'Tells you not to contact your university or DSO.',
      weight: 0.12,
      source_url: null,
      source_title: null,
    },
    {
      signal: 'fear_threat',
      text: 'Threatens arrest and deportation within 2 hours.',
      weight: 0.09,
    },
  ],
  tactics: ['authority', 'urgency', 'fear_threat', 'secrecy', 'payment_demand'],
  entities: {
    claimed_agency: 'ICE (Department of Homeland Security)',
    phone_numbers: ['+1 (202) 555-0147'],
    urls: ['http://sevis-verify-dhs.com/case'],
    emails: [],
    payment_methods: ['Gift cards (Target, Apple)'],
    amounts: ['$1,500'],
  },
  actions: GOV_ACTIONS.not_responded,
  report_text: `On October 7, 2026, I received a voicemail from someone who said he was "Officer James Miller, badge 4471" from the Department of Homeland Security / Immigration and Customs Enforcement (ICE). The caller ID showed "DHS Washington DC". He said my SEVIS record was flagged for termination and that a warrant for my arrest and deportation would be issued within 2 hours unless I paid a $1,500 "verification bond" in Target or Apple gift cards. He told me not to contact my university. He asked me to call back at +1 (202) 555-0147 and directed me to the website http://sevis-verify-dhs.com/case. I am an international student (F-1). I believe this was a government impersonation scam.`,
  sources: [
    {
      title: 'FTC: Gift card scams',
      url: 'https://consumer.ftc.gov/articles/gift-card-scams',
      snippet: 'Anyone who demands to be paid with a gift card is always a scammer.',
    },
    {
      title: 'USCIS: Scams, fraud and misconduct',
      url: 'https://www.uscis.gov/scams-fraud-and-misconduct',
      snippet: 'USCIS will never ask you to pay by phone or email, or to pay with gift cards or wire transfers.',
    },
    {
      title: 'DHS Study in the States',
      url: 'https://studyinthestates.dhs.gov/',
      snippet: 'Your DSO is your main point of contact for questions about your SEVIS record and F-1 status.',
    },
  ],
  language: 'en',
  llm_used: true,
  redacted_text: GOV_TEXT_REDACTED,
  extracted_text: null,
  latency_ms: 2140,
}

const optFraud: AnalyzeResponse = {
  ...govImpersonation,
  verdict: 'likely_scam',
  risk_score: 0.89,
  category: 'opt_employer_fraud',
  category_label: 'OPT employer fraud',
  category_probs: {
    opt_employer_fraud: 0.78,
    fake_job_task: 0.12,
    other_scam: 0.05,
    gov_impersonation: 0.01,
    legitimate: 0.04,
  },
  summary: 'This looks like a fake OPT job that charges you a fee.',
  explanation: `The "employer" offers a job with no interview and then asks you to pay $450 for an employer letter, I-983 training plan, and E-Verify processing. Real employers do not charge you for OPT paperwork, and E-Verify is free for employers.

They also ask for your passport, I-20, EAD, and SSN by email before you have started, and the payment goes to a Gmail address — not a company account.`,
  reasons: [
    {
      signal: 'violates_official_rule:employer_no_opt_fee',
      text: 'Asks you to pay a fee for an employer letter, I-983, or E-Verify. Legitimate employers never charge for this.',
      weight: 0.31,
      source_url: 'https://studyinthestates.dhs.gov/',
      source_title: 'DHS Study in the States',
    },
    {
      signal: 'advance_fee',
      text: 'You must pay $450 "refundable" fee before starting the job.',
      weight: 0.21,
      source_url: 'https://consumer.ftc.gov/articles/job-scams',
      source_title: 'FTC: Job scams',
    },
    {
      signal: 'pii_request',
      text: 'Asks for your passport, I-20, EAD, and SSN by email.',
      weight: 0.16,
    },
    {
      signal: 'free_email_payment',
      text: 'Payment goes to a Gmail address, not a company account.',
      weight: 0.1,
    },
  ],
  tactics: ['advance_fee', 'pii_request', 'urgency', 'too_good', 'payment_demand'],
  entities: {
    claimed_agency: null,
    phone_numbers: [],
    urls: [],
    emails: ['hr@techwave-solutions-usa.net', 'payments.techwave@gmail.com'],
    payment_methods: ['Zelle'],
    amounts: ['$450', '$38/hour'],
  },
  actions: [
    'Do not pay the fee and do not send your passport, I-20, EAD, or SSN.',
    'Stop replying to this "employer".',
    'Ask your DSO to look at the offer before you accept any OPT job. Use the contact details on your school\'s official website.',
    'Report the posting to the job site where you found it, and to ReportFraud.ftc.gov.',
  ],
  report_text:
    'I received an email from "Linda Carter, TechWave Solutions" (hr@techwave-solutions-usa.net) offering me a remote OPT job without an interview. They asked me to pay a $450 "processing fee" for an employer letter, I-983, and E-Verify via Zelle to payments.techwave@gmail.com within 24 hours, and to send my passport, I-20, EAD, and SSN. I believe this is an OPT employment scam.',
  sources: [
    {
      title: 'FTC: Job scams',
      url: 'https://consumer.ftc.gov/articles/job-scams',
      snippet: 'Never pay for the promise of a job. Legitimate employers will never ask you to pay to get a job.',
    },
    {
      title: 'DHS Study in the States',
      url: 'https://studyinthestates.dhs.gov/',
      snippet: 'Talk to your DSO before accepting OPT or STEM OPT employment.',
    },
  ],
  redacted_text: `From: HR Onboarding <hr@techwave-solutions-usa.net>
Subject: Congratulations - OPT Offer Letter & E-Verify Processing

... a one-time refundable processing fee of $450 is required. Please pay via Zelle to payments.techwave@gmail.com within 24 hours ... reply with a scan of your passport, I-20, and EAD card, and your SSN ...`,
  latency_ms: 1870,
}

const taskScam: AnalyzeResponse = {
  ...optFraud,
  verdict: 'likely_scam',
  risk_score: 0.93,
  category: 'fake_job_task',
  category_label: 'Fake job / task scam',
  category_probs: {
    fake_job_task: 0.86,
    other_scam: 0.07,
    opt_employer_fraud: 0.04,
    gov_impersonation: 0.0,
    legitimate: 0.03,
  },
  summary: 'This is very likely a "task" job scam.',
  explanation: `You are offered hundreds of dollars a day for liking and rating products, then asked to "recharge" your account with crypto to unlock bigger tasks. This is how task scams work: the early "earnings" are fake, and the deposits are never returned.

Unauthorized work can also put your F-1 status at risk, so be careful with any off-campus "job" offered over WhatsApp.`,
  reasons: [
    {
      signal: 'advance_fee',
      text: 'Asks you to deposit $100 in USDT (crypto) to unlock tasks.',
      weight: 0.3,
      source_url: 'https://consumer.ftc.gov/articles/job-scams',
      source_title: 'FTC: Job scams',
    },
    { signal: 'too_good', text: 'Promises $300-$800 per day for 20-30 minutes of work.', weight: 0.22 },
    { signal: 'unsolicited_messaging_app', text: 'Unsolicited job offer on WhatsApp from a foreign number.', weight: 0.14 },
    { signal: 'non_official_domain', text: 'Uses amz-taskhub.top, which is not an Amazon website.', weight: 0.12 },
  ],
  tactics: ['too_good', 'advance_fee', 'payment_demand', 'urgency'],
  entities: {
    claimed_agency: null,
    phone_numbers: ['+44 7700 900321'],
    urls: ['http://amz-taskhub.top'],
    emails: [],
    payment_methods: ['Crypto (USDT)'],
    amounts: ['$300-$800', '$100'],
  },
  actions: [
    'Do not register on the website and do not send any crypto.',
    'Block and report the number in WhatsApp.',
    'Talk to your DSO before taking any off-campus work — unauthorized employment can affect your F-1 status.',
    'Report it at ReportFraud.ftc.gov.',
  ],
  report_text:
    'I received an unsolicited WhatsApp message from +44 7700 900321 claiming to be "Emma from Amazon Partner Recruitment", offering $300-$800 per day to rate products and asking me to deposit $100 in USDT at http://amz-taskhub.top to unlock tasks. I believe this is a task-based job scam.',
  redacted_text:
    '[WhatsApp, +44 7700 900321] Hi! I\'m Emma from Amazon Partner Recruitment ... earn $300-$800 daily ... recharge your account with $100 in USDT (crypto) ...',
  latency_ms: 1650,
}

const legitimate: AnalyzeResponse = {
  verdict: 'likely_safe',
  risk_score: 0.12,
  category: 'legitimate',
  category_label: 'Looks legitimate',
  category_probs: {
    legitimate: 0.88,
    gov_impersonation: 0.05,
    other_scam: 0.04,
    opt_employer_fraud: 0.02,
    fake_job_task: 0.01,
  },
  summary: 'This looks like a normal reminder from your international student office.',
  explanation: `The message comes from a .edu address, asks you to log in through your school's own portal, and does not ask for money or personal numbers. It even says ISSS will never ask for payment or your SSN by phone or email.

It does have a deadline, but real SEVIS registration reminders often do. To be safe, open the portal yourself from your school's website instead of using links in emails.`,
  reasons: [
    { signal: 'official_domain', text: 'Sent from a university .edu address.', weight: -0.2 },
    { signal: 'no_payment_request', text: 'Does not ask for money, gift cards, or crypto.', weight: -0.18 },
    { signal: 'urgency', text: 'Has a deadline ("by Friday") — common in real reminders, but still worth checking.', weight: 0.06 },
  ],
  tactics: ['urgency'],
  entities: {
    claimed_agency: 'International Student & Scholar Services',
    phone_numbers: [],
    urls: [],
    emails: ['isss@university.edu'],
    payment_methods: [],
    amounts: [],
  },
  actions: [
    "Log in to the ISSS portal by typing your school's website address yourself, not through a link.",
    'Complete your SEVIS registration before the deadline.',
    'If anything feels off, call ISSS using the number on the official school website.',
  ],
  report_text: null,
  sources: [
    {
      title: 'DHS Study in the States',
      url: 'https://studyinthestates.dhs.gov/',
      snippet: 'Your DSO is your main point of contact for questions about your SEVIS record and F-1 status.',
    },
  ],
  language: 'en',
  llm_used: true,
  redacted_text:
    'From: International Student & Scholar Services <isss@university.edu>\nSubject: Reminder: Confirm your SEVIS registration for Fall 2026 by Friday ...',
  extracted_text: null,
  latency_ms: 1320,
}

export const MOCK_RESPONSE: AnalyzeResponse = govImpersonation

/** Picks a canned response that roughly matches the pasted text, so example chips demo well. */
export function pickMockResponse(text: string, language: string, situation: Situation): AnalyzeResponse {
  const t = text.toLowerCase()
  let base: AnalyzeResponse
  if (/isss|international student & scholar|no fee for sevis/.test(t)) base = legitimate
  else if (/usdt|crypto|whatsapp|rate products|task/.test(t)) base = taskScam
  else if (/opt|i-983|e-verify|employer letter|offer letter/.test(t)) base = optFraud
  else base = govImpersonation

  const actions = base === govImpersonation ? GOV_ACTIONS[situation] : base.actions
  return { ...base, actions, language }
}
