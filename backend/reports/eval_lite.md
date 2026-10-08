# VisaShield evaluation

Classifier: `fine-tuned DistilBERT (ONNX int8, lite runtime)` · Fusion: `trained (expert prior, lam=0.01)`

## Real-world TEST set (independently written, held out): 56 messages, 37 scams

| System | Precision | Recall | F1 | False-positive rate | Category macro-F1 |
|---|---|---|---|---|---|
| tfidf_baseline | 0.926 | 0.676 | 0.781 | 0.105 | 0.610 |
| fusion_no_classifier | 0.800 | 0.973 | 0.878 | 0.474 | 0.362 |
| fusion_no_verify | 0.931 | 0.730 | 0.818 | 0.105 | 0.771 |
| full_fusion | 0.967 | 0.784 | 0.866 | 0.053 | 0.859 |

## Real-world DEV set (used for error analysis and prior-strength selection): 62 messages, 44 scams

| System | Precision | Recall | F1 | False-positive rate | Category macro-F1 |
|---|---|---|---|---|---|
| tfidf_baseline | 0.967 | 0.659 | 0.784 | 0.056 | 0.576 |
| fusion_no_classifier | 0.860 | 0.977 | 0.915 | 0.389 | 0.452 |
| fusion_no_verify | 0.955 | 0.955 | 0.955 | 0.111 | 0.846 |
| full_fusion | 0.956 | 0.977 | 0.966 | 0.111 | 0.869 |

## In-distribution test split (public + synthetic): 666 messages, 386 scams

| System | Precision | Recall | F1 | False-positive rate | Category macro-F1 |
|---|---|---|---|---|---|
| tfidf_baseline | 0.968 | 0.953 | 0.961 | 0.043 | 0.961 |
| fusion_no_classifier | 0.827 | 0.632 | 0.717 | 0.182 | 0.312 |
| fusion_no_verify | 0.989 | 0.956 | 0.972 | 0.014 | 0.972 |
| full_fusion | 0.989 | 0.953 | 0.971 | 0.014 | 0.972 |

## Prompt-injection robustness (405 attacked scam messages)

- Full fusion flags the same scams **without** injected text: **88.9%**
- Full fusion still flags them **with** injected text: **89.9%**

## Errors on real_world_dev (full fusion)

- `other_scam` risk 0.085: From: Student Financial Services <sfs.billing.dept@outlook.com> Subject: FINAL NOTICE - unpaid tuition  Your spring registration and I-20 will be cancelled toda
- `legitimate` risk 0.85: From: SEVP Portal <sevp.portal@ice.dhs.gov> Subject: Action required: OPT employment information  Our records indicate you have accrued unemployment time on pos
- `legitimate` risk 0.818: Chase: Did you make a $412.99 purchase at BESTBUY.COM? Reply Y or N. To speak to us, call the number on the back of your card. We'll never ask for your password

