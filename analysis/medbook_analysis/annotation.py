"""
Annotation agreement (synopsis: 'two annotators where possible, report Cohen's kappa').

Usage:  python -m medbook_analysis.annotation annotator1.csv annotator2.csv
Both files use the labelled-CSV format (text + five aspect columns) with the SAME rows in the SAME order.
"""
from __future__ import annotations
import sys
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from .config import ASPECTS, LABELS


def kappa_report(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    if len(a) != len(b):
        raise ValueError("Annotator files must have the same number of rows.")
    if not (a["text"].str.strip().values == b["text"].str.strip().values).all():
        raise ValueError("Rows are not in the same order / texts differ between annotators.")
    rows = []
    for asp in ASPECTS:
        rows.append({"aspect": asp, "kappa": cohen_kappa_score(a[asp], b[asp], labels=LABELS),
                     "percent_agreement": 100 * float((a[asp].values == b[asp].values).mean())})
    out = pd.DataFrame(rows)
    out.loc[len(out)] = {"aspect": "MEAN", "kappa": out["kappa"].mean(), "percent_agreement": out["percent_agreement"].mean()}
    return out


def interpret(k: float) -> str:  # Landis & Koch (1977) bands
    return ("poor" if k < 0 else "slight" if k <= .2 else "fair" if k <= .4 else "moderate" if k <= .6
            else "substantial" if k <= .8 else "almost perfect")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    r = kappa_report(pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[2]))
    r["interpretation"] = r["kappa"].map(interpret)
    print(r.round(3).to_string(index=False))
