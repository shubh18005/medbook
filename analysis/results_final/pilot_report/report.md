# MedBook study analysis

Submissions analysed: **69**

## RQ1 - response rate
| group | responses | participants | rate_pct | ci_low_pct | ci_high_pct |
|---|---|---|---|---|---|
| A | 8 | 40 | 20.0 | 10.5 | 34.757 |
| B | 21 | 40 | 52.5 | 37.497 | 67.065 |
| C | 23 | 40 | 57.5 | 42.195 | 71.491 |
| D | 17 | 40 | 42.5 | 28.509 | 57.805 |

chi2(3) = 13.53, p = 0.0036, Cramer's V = 0.29

Pairwise Fisher exact (Holm-corrected):
| a | b | odds_ratio | p_fisher | p_holm |
|---|---|---|---|---|
| A | B | 0.226 | 0.005 | 0.024 |
| A | C | 0.185 | 0.001 | 0.007 |
| A | D | 0.338 | 0.053 | 0.21 |
| B | C | 0.817 | 0.822 | 1.0 |
| B | D | 1.495 | 0.502 | 1.0 |
| C | D | 1.83 | 0.263 | 0.79 |

## RQ2 - content of feedback
Neutral share (overall rating = 3):
| study_group | sum | count | neutral_pct |
|---|---|---|---|
| A | 1 | 8 | 12.5 |
| B | 3 | 21 | 14.286 |
| C | 6 | 23 | 26.087 |
| D | 3 | 17 | 17.647 |

**overall_rating**: Kruskal-Wallis H = 3.12, p = 0.3740, epsilon^2 = 0.002; medians {'A': 4.0, 'B': 4.0, 'C': 4.0, 'D': 4.0}

| a | b | p_mwu | p_holm | cliffs_delta |
|---|---|---|---|---|
| A | B | 0.859 | 1.0 | -0.048 |
| A | C | 0.944 | 1.0 | -0.022 |
| A | D | 0.173 | 0.867 | -0.331 |
| B | C | 0.961 | 1.0 | 0.01 |
| B | D | 0.232 | 0.926 | -0.218 |
| C | D | 0.096 | 0.575 | -0.299 |

**word_count**: Kruskal-Wallis H = 1.67, p = 0.6428, epsilon^2 = 0.000; medians {'A': 11.5, 'B': 8.0, 'C': 12.0, 'D': 10.0}

| a | b | p_mwu | p_holm | cliffs_delta |
|---|---|---|---|---|
| A | B | 0.325 | 1.0 | 0.244 |
| A | C | 0.785 | 1.0 | 0.071 |
| A | D | 0.704 | 1.0 | 0.103 |
| B | C | 0.302 | 1.0 | -0.182 |
| B | D | 0.382 | 1.0 | -0.168 |
| C | D | 0.923 | 1.0 | 0.02 |

**aspects_mentioned**: Kruskal-Wallis H = 0.08, p = 0.9940, epsilon^2 = 0.000; medians {'A': 1.0, 'B': 1.0, 'C': 1.0, 'D': 1.0}

| a | b | p_mwu | p_holm | cliffs_delta |
|---|---|---|---|---|
| A | B | 0.878 | 1.0 | 0.042 |
| A | C | 0.981 | 1.0 | 0.011 |
| A | D | 0.855 | 1.0 | 0.051 |
| B | C | 0.863 | 1.0 | -0.031 |
| B | D | 0.988 | 1.0 | 0.006 |
| C | D | 0.841 | 1.0 | 0.038 |

## RQ3 - quality gate
Low-effort share (Q < 0.5) %: {'A': 0.0, 'B': 38.1, 'C': 34.78, 'D': 41.18}

Quality score Q: H = 1.57, p = 0.6654, epsilon^2 = 0.000; medians {'A': 0.71835, 'B': 0.6767, 'C': 0.7133, 'D': 0.5633}

| a | b | p_mwu | p_holm | cliffs_delta |
|---|---|---|---|---|
| A | B | 0.418 | 1.0 | 0.202 |
| A | C | 0.309 | 1.0 | 0.25 |
| A | D | 0.144 | 0.865 | 0.375 |
| B | C | 0.777 | 1.0 | -0.052 |
| B | D | 0.848 | 1.0 | -0.039 |
| C | D | 0.924 | 1.0 | 0.02 |

## RQ4 - hidden negatives
Reviews with text: 68
- Mixed-review rate (MR): **11.8%**
- Masked-negative rate (MNR): **39.1%**
- McNemar (overall vs aspect view): only-overall=2, only-aspect=12, p = 0.01294
- Share of reviews with a negative sentiment per aspect (%): {'doctor': 4.41, 'staff': 16.18, 'waiting': 13.24, 'cleanliness': 10.29, 'billing': 8.82}

## Model comparison (held-out labelled test set)
| model | macro_f1 | macro_f1_polarity | missed_negative_pct | latency_ms | n_test |
|---|---|---|---|---|---|
| TF-IDF + LR | 0.352 | 0.219 | 61.111 | 6.757 | 35 |
| TF-IDF + SVM | 0.387 | 0.257 | 61.111 | 6.42 | 35 |
| Clause rules (hybrid) | 0.624 | 0.565 | 33.333 | 0.324 | 35 |
