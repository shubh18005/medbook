| model                 | train                                      | test           |   accuracy |   macro_f1_4class |   macro_f1_polarity |   missed_negative_pct |   cv_sd_macro_f1_polarity |
|:----------------------|:-------------------------------------------|:---------------|-----------:|------------------:|--------------------:|----------------------:|--------------------------:|
| TF-IDF + LR           | A: synthetic only                          | real28         |      0.693 |             0.438 |               0.293 |                46.667 |                   nan     |
| TF-IDF + LR           | A: synthetic only                          | real24_unique  |      0.7   |             0.429 |               0.285 |                58.333 |                   nan     |
| TF-IDF + LR           | B: synthetic + handwritten                 | real28         |      0.757 |             0.446 |               0.299 |                46.667 |                   nan     |
| TF-IDF + LR           | B: synthetic + handwritten                 | real24_unique  |      0.75  |             0.434 |               0.284 |                58.333 |                   nan     |
| TF-IDF + SVM          | A: synthetic only                          | real28         |      0.7   |             0.452 |               0.307 |                40     |                   nan     |
| TF-IDF + SVM          | A: synthetic only                          | real24_unique  |      0.708 |             0.449 |               0.305 |                50     |                   nan     |
| TF-IDF + SVM          | B: synthetic + handwritten                 | real28         |      0.764 |             0.473 |               0.333 |                40     |                   nan     |
| TF-IDF + SVM          | B: synthetic + handwritten                 | real24_unique  |      0.758 |             0.465 |               0.324 |                50     |                   nan     |
| Clause rules (hybrid) | none (rule-based)                          | real28         |      0.929 |             0.712 |               0.67  |                 6.667 |                   nan     |
| Clause rules (hybrid) | none (rule-based)                          | real24_unique  |      0.917 |             0.704 |               0.66  |                 8.333 |                   nan     |
| Clause rules (hybrid) | none (rule-based)                          | handwritten87  |      0.862 |             0.784 |               0.775 |                23.913 |                   nan     |
| Majority ('absent')   | -                                          | real28         |      0.429 |             0.148 |             nan     |               100     |                   nan     |
| TF-IDF + LR           | C: 3x5-fold CV (real24+hand87, +synthetic) | held-out folds |      0.8   |             0.518 |               0.406 |                44.417 |                     0.084 |
| TF-IDF + SVM          | C: 3x5-fold CV (real24+hand87, +synthetic) | held-out folds |      0.803 |             0.54  |               0.437 |                44.953 |                     0.088 |

Per-aspect (clause rules, test real28):

| aspect      |   precision |   recall |    f1 |   f1_polarity_mentioned |
|:------------|------------:|---------:|------:|------------------------:|
| doctor      |       0.737 |    0.75  | 0.743 |                   0.658 |
| staff       |       0.543 |    0.677 | 0.567 |                   0.653 |
| waiting     |       0.679 |    0.679 | 0.678 |                   0.586 |
| cleanliness |       0.977 |    0.917 | 0.938 |                   0.933 |
| billing     |       0.708 |    0.597 | 0.632 |                   0.519 |
| MACRO       |       0.729 |    0.724 | 0.712 |                   0.67  |

RQ4 on real data:

```
{
 "n": 28,
 "gold": {
  "MR": 0.35714285714285715,
  "MNR": 0.6666666666666666,
  "n_with_negative_aspect": 15
 },
 "model_clause_rules": {
  "MR": 0.39285714285714285,
  "MNR": 0.7333333333333333
 },
 "gold_unique24": {
  "n": 24,
  "MR": 0.2916666666666667,
  "MNR": 0.6666666666666666
 },
 "mcnemar_gold": {
  "both": 3,
  "only_overall": 0,
  "only_aspect": 12,
  "statistic": 0.0,
  "p_value": 0.00048828125
 }
}
```
