"""
Statistical plan (synopsis Section 5.3.2 / paper Section V-B).

 RQ1  response rate across groups : chi-square, or an exact/permutation version when counts are small,
                                    pairwise Fisher exact tests with Holm correction
 RQ2/3 rating, text length, neutral share, aspect coverage : Kruskal-Wallis + pairwise Mann-Whitney (Holm)
 RQ4  paired masked-negative rates : McNemar (see measures.py)
 Effect sizes and confidence intervals are returned next to every p-value, because groups are small.
"""
from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from scipy import stats
from ._compat import multipletests_holm, wilson


def holm(pvals):
    return multipletests_holm(pvals) if len(pvals) else np.array([])


# ------------------------------------------------------------------ RQ1
def response_rate_table(counts: dict) -> pd.DataFrame:
    """counts: {'A': (responses, participants), ...} -> rate with Wilson 95% CI."""
    rows = []
    for g, (r, n) in counts.items():
        lo, hi = wilson(r, n) if n else (np.nan, np.nan)
        rows.append({"group": g, "responses": r, "participants": n,
                     "rate_pct": 100 * r / n if n else np.nan, "ci_low_pct": 100 * lo, "ci_high_pct": 100 * hi})
    return pd.DataFrame(rows)


def response_rate_tests(counts: dict, n_perm: int = 20000, seed: int = 0) -> dict:
    groups = list(counts)
    table = np.array([[counts[g][0], counts[g][1] - counts[g][0]] for g in groups])
    chi2, p, dof, expected = stats.chi2_contingency(table, correction=False)
    small = bool((expected < 5).any())
    out = {"chi2": float(chi2), "dof": int(dof), "p_chi2": float(p), "small_expected_counts": small}
    n = table.sum()
    out["cramers_v"] = float(np.sqrt(chi2 / (n * (min(table.shape) - 1)))) if n else float("nan")
    if small:  # Monte-Carlo permutation p-value of the chi-square statistic (exact test stand-in for r x 2 tables)
        rng = np.random.RandomState(seed)
        labels = np.concatenate([[i] * int(table[i].sum()) for i in range(len(groups))])
        outcome = np.concatenate([[1] * int(table[i, 0]) + [0] * int(table[i, 1]) for i in range(len(groups))])
        ge = 0
        for _ in range(n_perm):
            rng.shuffle(outcome)
            t = np.array([[outcome[labels == i].sum(), (labels == i).sum() - outcome[labels == i].sum()]
                          for i in range(len(groups))])
            try:
                c = stats.chi2_contingency(t, correction=False)[0]
            except ValueError:
                continue
            ge += c >= chi2 - 1e-12
        out["p_permutation"] = float((ge + 1) / (n_perm + 1))
    pairs, ps = [], []
    for a, b in itertools.combinations(groups, 2):
        t = [[counts[a][0], counts[a][1] - counts[a][0]], [counts[b][0], counts[b][1] - counts[b][0]]]
        odds, pf = stats.fisher_exact(t)
        pairs.append((a, b, float(odds)))
        ps.append(pf)
    adj = holm(ps)
    out["pairwise"] = [{"a": a, "b": b, "odds_ratio": o, "p_fisher": float(p_), "p_holm": float(ph)}
                       for (a, b, o), p_, ph in zip(pairs, ps, adj)]
    return out


# ------------------------------------------------------------------ RQ2 / RQ3
def cliffs_delta(x, y) -> float:
    x, y = np.asarray(x), np.asarray(y)
    if len(x) == 0 or len(y) == 0:
        return float("nan")
    u = stats.mannwhitneyu(x, y, alternative="two-sided").statistic
    return float(2 * u / (len(x) * len(y)) - 1)


def kruskal_with_posthoc(df: pd.DataFrame, value: str, group: str = "study_group") -> dict:
    d = df[[group, value]].dropna()
    samples = {g: v[value].values for g, v in d.groupby(group)}
    if len(samples) < 2 or any(len(v) < 2 for v in samples.values()):
        return {"note": "not enough data in at least one group", "n_per_group": {g: len(v) for g, v in samples.items()}}
    if np.ptp(np.concatenate(list(samples.values()))) == 0:
        return {"note": "all values identical", "n_per_group": {g: len(v) for g, v in samples.items()}}
    H, p = stats.kruskal(*samples.values())
    n, k = len(d), len(samples)
    eps2 = float(max(0.0, (H - k + 1) / (n - k))) if n > k else float("nan")   # epsilon-squared effect size
    pairs, ps = [], []
    for a, b in itertools.combinations(samples, 2):
        try:
            pu = stats.mannwhitneyu(samples[a], samples[b], alternative="two-sided").pvalue
        except ValueError:
            pu = 1.0
        pairs.append((a, b)); ps.append(pu)
    adj = holm(ps)
    return {"H": float(H), "p": float(p), "epsilon_sq": eps2,
            "medians": {g: float(np.median(v)) for g, v in samples.items()},
            "pairwise": [{"a": a, "b": b, "p_mwu": float(p_), "p_holm": float(ph),
                          "cliffs_delta": cliffs_delta(samples[a], samples[b])}
                         for (a, b), p_, ph in zip(pairs, ps, adj)]}


def neutral_share_by_group(df: pd.DataFrame, group: str = "study_group") -> pd.DataFrame:
    """Neutral share = share of submissions whose overall star rating is 3."""
    t = df.assign(is_neutral=(df["overall_rating"] == 3).astype(int))
    g = t.groupby(group)["is_neutral"].agg(["sum", "count"])
    g["neutral_pct"] = 100 * g["sum"] / g["count"]
    return g.reset_index()
