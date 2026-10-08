import type { Example } from './types'

/** Used when GET /api/examples fails or returns nothing. All numbers/domains are fictional. */
export const FALLBACK_EXAMPLES: Example[] = [
  {
    title: 'Fake ICE / SEVIS call',
    label: 'gov_impersonation',
    text: `Call transcript (voicemail, caller ID showed "DHS Washington DC"):
"This is Officer James Miller, badge number 4471, from the Department of Homeland Security, Immigration and Customs Enforcement. This call is regarding your SEVIS record. Our system shows discrepancies in your F-1 status and your SEVIS ID has been flagged for termination. A warrant will be issued for your arrest and deportation within 2 hours unless you resolve this today. Do NOT contact your university or your DSO, this is a confidential federal investigation and telling anyone will make your case worse. To clear the flag you must pay a verification bond of $1,500 using Target or Apple gift cards. Call me back immediately at +1 (202) 555-0147 and stay on the line. You can also verify your case at http://sevis-verify-dhs.com/case."`,
  },
  {
    title: 'OPT employer-letter fee',
    label: 'opt_employer_fraud',
    text: `From: HR Onboarding <hr@techwave-solutions-usa.net>
Subject: Congratulations - OPT Offer Letter & E-Verify Processing

Dear Candidate,

We are pleased to offer you the position of Remote Data Analyst (OPT/STEM OPT eligible) at TechWave Solutions, $38/hour. No interview is needed as your profile already matches our requirements.

To issue your official employer letter and complete your I-983 training plan and E-Verify registration, a one-time refundable processing fee of $450 is required. Please pay via Zelle to payments.techwave@gmail.com within 24 hours, or the offer will be given to another candidate. The fee will be reimbursed in your first paycheck.

Please also reply with a scan of your passport, I-20, and EAD card, and your SSN, so we can start onboarding.

Best regards,
Linda Carter
Talent Acquisition, TechWave Solutions`,
  },
  {
    title: 'WhatsApp task job',
    label: 'fake_job_task',
    text: `[WhatsApp, +44 7700 900321]
Hi! I'm Emma from Amazon Partner Recruitment. We found your resume on Handshake. We have a flexible part-time remote job for students: just like and rate products online, 20-30 min per day, earn $300-$800 daily, paid same day! No experience or visa sponsorship needed.
To start, register at http://amz-taskhub.top and complete 3 trial tasks. For premium tasks you need to recharge your account with $100 in USDT (crypto) to unlock higher commissions — you will get it back with 30% profit. Limited spots today only! Reply YES to begin.`,
  },
  {
    title: 'Genuine DSO reminder',
    label: 'legitimate',
    text: `From: International Student & Scholar Services <isss@university.edu>
Subject: Reminder: Confirm your SEVIS registration for Fall 2026 by Friday

Dear F-1 Student,

This is a reminder that all continuing F-1 students must complete Fall 2026 SEVIS registration by Friday, September 18. Please log in to the ISSS student portal (linked from the ISSS page on the university website) and confirm your US address and enrollment.

If you do not register, your SEVIS record may be affected, so please complete this soon. There is no fee for SEVIS registration, and ISSS will never ask you for payment, gift cards, or your SSN by phone or email.

If you have questions, visit us during walk-in advising hours or call the number listed on the ISSS website.

International Student & Scholar Services`,
  },
]
