"""
RQ4 measures (synopsis Section 5.2.4, eqs. 5.2 and 5.3).

  MR  = N_mixed  / N_all     reviews with >=1 positive AND >=1 negative aspect
  MNR = N_masked / N_neg     among reviews with >=1 negative aspect, those whose OVERALL label is positive
"""
from __future__ import annotations
import pandas as pd
from ._compat import mcnemar
from .config import ASPECTS, overall_label


def overall_labels(stars: pd.Series) -> pd.Series:
    return stars.astype(int).map(overall_label)


def mixed_review_rate(asp: pd.DataFrame) -> float:
    has_pos = (asp[ASPECTS] == "positive").any(axis=1)
    has_neg = (asp[ASPECTS] == "negative").any(axis=1)
    return float((has_pos & has_neg).sum() / max(len(asp), 1))


def masked_negative_rate(asp: pd.DataFrame, overall: pd.Series) -> float:
    has_neg = (asp[ASPECTS] == "negative").any(axis=1)
    masked = has_neg & (overall.values == "positive")
    return float(masked.sum() / max(has_neg.sum(), 1))


def missed_negative_rate(true_asp: pd.DataFrame, pred_asp: pd.DataFrame) -> float:
    """Share of reviews with a truly negative aspect where the aspect model flags NO negative
    aspect (this is what Table V calls the masked-negative rate 'for the aspect models')."""
    t = (true_asp[ASPECTS] == "negative").any(axis=1)
    p = (pred_asp[ASPECTS] == "negative").any(axis=1)
    return float((t & ~p).sum() / max(t.sum(), 1))


def overall_view_missed_rate(true_asp: pd.DataFrame, overall: pd.Series) -> float:
    """Share of reviews with a truly negative aspect where the overall-level view is not negative."""
    t = (true_asp[ASPECTS] == "negative").any(axis=1)
    miss = t & (overall.values != "negative")
    return float(miss.sum() / max(t.sum(), 1))


def mcnemar_overall_vs_aspect(asp_pred: pd.DataFrame, overall: pd.Series) -> dict:
    """
    Paired comparison on the SAME reviews (RQ4 / H4). Population = reviews that at least one view
    flags as having a problem (overall label negative, or any negative aspect predicted).
    Discordant pairs: only-overall-flags vs only-aspect-flags. Exact McNemar test on those.
    """
    ov = (overall.values == "negative")
    asp = (asp_pred[ASPECTS] == "negative").any(axis=1).values
    pop = ov | asp
    n11 = int((ov & asp & pop).sum())
    n10 = int((ov & ~asp & pop).sum())   # only overall flags
    n01 = int((~ov & asp & pop).sum())   # only aspect flags
    n00 = 0
    table = [[n11, n10], [n01, n00]]
    res = mcnemar(table, exact=True)
    return {"both": n11, "only_overall": n10, "only_aspect": n01,
            "statistic": float(res.statistic), "p_value": float(res.pvalue)}


def rq4_summary(asp_pred: pd.DataFrame, stars: pd.Series) -> dict:
    ov = overall_labels(stars)
    return {
        "n_reviews": int(len(asp_pred)),
        "mixed_review_rate": mixed_review_rate(asp_pred),
        "masked_negative_rate": masked_negative_rate(asp_pred, ov),
        "mcnemar": mcnemar_overall_vs_aspect(asp_pred, ov),
    }
