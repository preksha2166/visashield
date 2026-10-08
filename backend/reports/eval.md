# VisaShield evaluation

Classifier: `fine-tuned DistilBERT` · Fusion: `trained (expert prior, lam=0.01)`

## Real-world TEST set (independently written, held out): 56 messages, 37 scams

| System | Precision | Recall | F1 | False-positive rate | Category macro-F1 |
|---|---|---|---|---|---|
| tfidf_baseline | 0.926 | 0.676 | 0.781 | 0.105 | 0.610 |
| transformer | 0.933 | 0.757 | 0.836 | 0.105 | 0.816 |
| fusion_no_classifier | 0.800 | 0.973 | 0.878 | 0.474 | 0.362 |
| fusion_no_verify | 0.935 | 0.784 | 0.853 | 0.105 | 0.804 |
| full_fusion | 0.969 | 0.838 | 0.899 | 0.053 | 0.876 |

## Real-world DEV set (used for error analysis and prior-strength selection): 62 messages, 44 scams

| System | Precision | Recall | F1 | False-positive rate | Category macro-F1 |
|---|---|---|---|---|---|
| tfidf_baseline | 0.967 | 0.659 | 0.784 | 0.056 | 0.576 |
| transformer | 0.933 | 0.955 | 0.944 | 0.167 | 0.819 |
| fusion_no_classifier | 0.860 | 0.977 | 0.915 | 0.389 | 0.452 |
| fusion_no_verify | 0.955 | 0.955 | 0.955 | 0.111 | 0.813 |
| full_fusion | 0.956 | 0.977 | 0.966 | 0.111 | 0.835 |

## In-distribution test split (public + synthetic): 666 messages, 386 scams

| System | Precision | Recall | F1 | False-positive rate | Category macro-F1 |
|---|---|---|---|---|---|
| tfidf_baseline | 0.968 | 0.953 | 0.961 | 0.043 | 0.961 |
| transformer | 0.984 | 0.961 | 0.972 | 0.021 | 0.974 |
| fusion_no_classifier | 0.827 | 0.632 | 0.717 | 0.182 | 0.312 |
| fusion_no_verify | 0.987 | 0.961 | 0.974 | 0.018 | 0.975 |
| full_fusion | 0.987 | 0.959 | 0.972 | 0.018 | 0.975 |

## Prompt-injection robustness (405 attacked scam messages)

- Full fusion flags the same scams **without** injected text: **91.4%**
- Full fusion still flags them **with** injected text: **89.1%**

## Errors on real_world_test (full fusion)

- `gov_impersonation` risk 0.162: so weird thing happened. my phone showed the university's main number calling so I picked up. the guy said he was from the 'international compliance unit' and t
- `gov_impersonation` risk 0.084: From: IRS Refunds <refunds@irs-taxrefund-center.com> Subject: Tax Refund Payment - Action Required for .edu Account Holders  Our records indicate you are eligib
- `gov_impersonation` risk 0.499: From: Office of International Students <intl.student.office.advising@gmail.com> Subject: URGENT: Your I-20 has been flagged  Hello,  During our fall SEVIS audit
- `fake_job_task` risk 0.029: I thought it was a real side job. The app had me 'boost' hotel listings by rating them, and the first two days I actually got $35 and $52 sent to my account. On
- `fake_job_task` risk 0.034: From: Prof. Helen Marsh <helenmarsh.research.lab@gmail.com> Subject: RESEARCH ASSISTANT  Hello,  I am looking for a student research assistant to help with data
- `other_scam` risk 0.173: From: Global Tuition Partners <payments@globaltuitionpartners.co> Subject: Save 15% on your Spring tuition - authorized university payment agent  Dear Student, 
- `legitimate` risk 0.688: UNO Alert: Students have reported calls from people claiming to be ICE, IRS, CBP, FBI or local police saying your immigration status is in jeopardy. Government 

## Errors on real_world_dev (full fusion)

- `other_scam` risk 0.085: From: Student Financial Services <sfs.billing.dept@outlook.com> Subject: FINAL NOTICE - unpaid tuition  Your spring registration and I-20 will be cancelled toda
- `legitimate` risk 0.856: From: SEVP Portal <sevp.portal@ice.dhs.gov> Subject: Action required: OPT employment information  Our records indicate you have accrued unemployment time on pos
- `legitimate` risk 0.821: Chase: Did you make a $412.99 purchase at BESTBUY.COM? Reply Y or N. To speak to us, call the number on the back of your card. We'll never ask for your password

