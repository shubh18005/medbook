"""Aspect-wise precision / recall / F1 and latency (synopsis Table III, 'Models' row)."""
from __future__ import annotations
import time
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, f1_score
from .config import ASPECTS, LABELS


def aspect_report(y_true: pd.DataFrame, y_pred: pd.DataFrame) -> pd.DataFrame:
    """One row per aspect: macro P/R/F1 over all four labels + macro-F1 over the three
    polarity labels on aspects that are actually mentioned (the number that matters for ABSA)."""
    y_true, y_pred = y_true.reset_index(drop=True), y_pred.reset_index(drop=True)
    rows = []
    for a in ASPECTS:
        p, r, f, _ = precision_recall_fscore_support(y_true[a], y_pred[a], labels=LABELS,
                                                     average="macro", zero_division=0)
        m = y_true[a] != "absent"
        f_pol = f1_score(y_true[a][m], y_pred[a][m], labels=["negative", "neutral", "positive"],
                         average="macro", zero_division=0) if m.any() else float("nan")
        rows.append({"aspect": a, "precision": p, "recall": r, "f1": f, "f1_polarity_mentioned": f_pol})
    df = pd.DataFrame(rows)
    df.loc[len(df)] = {"aspect": "MACRO", **{c: df[c].mean() for c in df.columns if c != "aspect"}}
    return df


def latency_ms(predict_fn, texts, repeats: int = 3) -> float:
    """Mean wall-clock milliseconds per review (one review at a time, as in deployment)."""
    sample = list(texts)[:100]
    best = float("inf")
    for _ in range(repeats):
        t = time.perf_counter()
        for s in sample:
            predict_fn([s])
        best = min(best, (time.perf_counter() - t) / len(sample) * 1000)
    return best


def split(df: pd.DataFrame, test_frac: float = 0.3, seed: int = 42):
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(df))
    cut = int(len(df) * (1 - test_frac))
    return df.iloc[idx[:cut]].reset_index(drop=True), df.iloc[idx[cut:]].reset_index(drop=True)
