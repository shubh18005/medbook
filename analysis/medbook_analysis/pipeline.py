"""
End-to-end analysis (synopsis Section 6.3): backend CSV export  ->  RQ1..RQ4 results + model comparison.

Examples
  # study analysis with the TF-IDF model trained on a labelled file
  python -m medbook_analysis.pipeline --export medbook-feedback-export.csv \
         --participants A=40,B=40,C=40,D=40 --train-data data/labelled.csv --model tfidf-svm --out report

  # also compare TF-IDF vs a fine-tuned DistilBERT saved by bert_model.py
  python -m medbook_analysis.pipeline ... --model bert:models/distilbert

Response rate (RQ1) needs the number of participants per group, because the export only contains
people who responded. The admin 'Feedback Study' tab shows these counts.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import numpy as np
import pandas as pd
from .config import ASPECTS
from . import measures as M, stats_tests as S
from .baseline import TfidfAspectModel
from .evaluate import split, aspect_report, latency_ms
from .synth import load_labelled

RENAME = {"studyId": "study_id", "group": "study_group", "overallRating": "overall_rating", "freeText": "free_text",
          "wordCount": "word_count", "aspectsMentioned": "aspects_mentioned", "qualityQ": "quality_q",
          "detailD": "detail_d", "uniquenessU": "uniqueness_u", "consistencyC": "consistency_c",
          "gatePassed": "gate_passed", "rewardType": "reward_type", "rewardStatus": "reward_status"}


def load_export(path: str) -> pd.DataFrame:
    df = pd.read_csv(path).rename(columns=RENAME)
    need = ["study_group", "overall_rating", "free_text", "word_count", "aspects_mentioned", "quality_q"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"Export is missing columns {miss}. Use GET /api/feedback/export from the admin tab.")
    df["free_text"] = df["free_text"].fillna("").astype(str)
    # the backend prefixes ' to cells starting with = + - @ (spreadsheet-injection guard): undo it
    df["free_text"] = df["free_text"].str.replace(r"^'(?=[=+\-@\t\r])", "", regex=True)
    return df


def parse_participants(s: str) -> dict:
    return {k: int(v) for k, v in (kv.split("=") for kv in s.split(","))}


def get_model(spec: str, train_df: pd.DataFrame | None):
    if spec.startswith("bert:"):
        from .bert_model import BertAspectModel
        return BertAspectModel.load(spec[5:])
    if spec == "clause":
        from .clause_model import ClauseAspectModel
        return ClauseAspectModel()
    kind = {"tfidf-lr": "lr", "tfidf-svm": "svm"}.get(spec)
    if kind is None:
        raise ValueError("--model must be clause, tfidf-lr, tfidf-svm or bert:<dir>")
    if train_df is None:
        raise ValueError("--train-data is required for the TF-IDF models")
    return TfidfAspectModel(kind).fit(train_df)


def model_comparison(labelled: pd.DataFrame, extra_bert_dir: str | None, seed: int = 42) -> pd.DataFrame:
    """Table V analogue: same held-out test set for every model."""
    tr, te = split(labelled, seed=seed)
    rows = []
    from .clause_model import ClauseAspectModel
    cands = {"TF-IDF + LR": TfidfAspectModel("lr").fit(tr), "TF-IDF + SVM": TfidfAspectModel("svm").fit(tr),
             "Clause rules (hybrid)": ClauseAspectModel()}
    if extra_bert_dir:
        from .bert_model import BertAspectModel
        cands["DistilBERT/BERT"] = BertAspectModel.load(extra_bert_dir)
    for name, m in cands.items():
        pred = m.predict(te["text"])
        rep = aspect_report(te, pred).set_index("aspect")
        rows.append({"model": name, "macro_f1": rep.loc["MACRO", "f1"],
                     "macro_f1_polarity": rep.loc["MACRO", "f1_polarity_mentioned"],
                     "missed_negative_pct": 100 * M.missed_negative_rate(te, pred),
                     "latency_ms": latency_ms(m.predict, te["text"]), "n_test": len(te)})
    return pd.DataFrame(rows)


def analyse(export: pd.DataFrame, model, participants: dict | None, low_effort_q: float = 0.5) -> dict:
    res: dict = {"n_submissions": int(len(export))}
    # RQ1
    if participants:
        counts = {g: (int((export["study_group"] == g).sum()), n) for g, n in sorted(participants.items())}
        res["rq1"] = {"table": S.response_rate_table(counts).to_dict("records"), "tests": S.response_rate_tests(counts)}
    else:
        res["rq1"] = {"note": "pass --participants A=n,B=n,C=n,D=n to compute response rates"}
    # RQ2
    res["rq2"] = {"neutral_share": S.neutral_share_by_group(export).to_dict("records"),
                  "overall_rating": S.kruskal_with_posthoc(export, "overall_rating"),
                  "word_count": S.kruskal_with_posthoc(export, "word_count"),
                  "aspects_mentioned": S.kruskal_with_posthoc(export, "aspects_mentioned")}
    # RQ3
    low = export.assign(low_effort=(export["quality_q"] < low_effort_q).astype(int))
    res["rq3"] = {"quality_q": S.kruskal_with_posthoc(export, "quality_q"),
                  "low_effort_threshold_q": low_effort_q,
                  "low_effort_share_pct": (100 * low.groupby("study_group")["low_effort"].mean()).round(2).to_dict()}
    # RQ4: reviews that actually have text
    txt = export[export["free_text"].str.strip().str.len() > 0].reset_index(drop=True)
    if len(txt):
        asp = model.predict(txt["free_text"])
        res["rq4"] = M.rq4_summary(asp, txt["overall_rating"])
        res["rq4"]["aspect_negative_share_pct"] = {a: round(100 * float((asp[a] == "negative").mean()), 2) for a in ASPECTS}
    else:
        res["rq4"] = {"note": "no free-text submissions yet"}
    return res


def _md_table(df: pd.DataFrame) -> str:
    df = df.round(3)
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def write_report(res: dict, comparison: pd.DataFrame | None, out_dir: str, synthetic_warning: bool):
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "results.json"), "w"), indent=2, default=str)
    L = ["# MedBook study analysis", ""]
    if synthetic_warning:
        L += ["> **Warning:** the model was trained/evaluated on SYNTHETIC template data. Do not report these "
              "numbers as evidence about real patients.", ""]
    L += [f"Submissions analysed: **{res['n_submissions']}**", "", "## RQ1 - response rate"]
    r1 = res["rq1"]
    if "table" in r1:
        t = r1["tests"]
        L += [_md_table(pd.DataFrame(r1["table"])), "",
              f"chi2({t['dof']}) = {t['chi2']:.2f}, p = {t['p_chi2']:.4f}, Cramer's V = {t['cramers_v']:.2f}"
              + (f", permutation p = {t['p_permutation']:.4f} (small expected counts)" if "p_permutation" in t else ""), "",
              "Pairwise Fisher exact (Holm-corrected):", _md_table(pd.DataFrame(t["pairwise"])), ""]
    else:
        L += [r1["note"], ""]
    L += ["## RQ2 - content of feedback", "Neutral share (overall rating = 3):", _md_table(pd.DataFrame(res["rq2"]["neutral_share"])), ""]
    for k in ("overall_rating", "word_count", "aspects_mentioned"):
        v = res["rq2"][k]
        if "H" in v:
            L += [f"**{k}**: Kruskal-Wallis H = {v['H']:.2f}, p = {v['p']:.4f}, epsilon^2 = {v['epsilon_sq']:.3f}; medians {v['medians']}", "",
                  _md_table(pd.DataFrame(v["pairwise"])), ""]
        else:
            L += [f"**{k}**: {v.get('note')}", ""]
    L += ["## RQ3 - quality gate", f"Low-effort share (Q < {res['rq3']['low_effort_threshold_q']}) %: {res['rq3']['low_effort_share_pct']}", ""]
    v = res["rq3"]["quality_q"]
    if "H" in v:
        L += [f"Quality score Q: H = {v['H']:.2f}, p = {v['p']:.4f}, epsilon^2 = {v['epsilon_sq']:.3f}; medians {v['medians']}", "",
              _md_table(pd.DataFrame(v["pairwise"])), ""]
    L += ["## RQ4 - hidden negatives"]
    r4 = res["rq4"]
    if "mixed_review_rate" in r4:
        m = r4["mcnemar"]
        L += [f"Reviews with text: {r4['n_reviews']}",
              f"- Mixed-review rate (MR): **{100 * r4['mixed_review_rate']:.1f}%**",
              f"- Masked-negative rate (MNR): **{100 * r4['masked_negative_rate']:.1f}%**",
              f"- McNemar (overall vs aspect view): only-overall={m['only_overall']}, only-aspect={m['only_aspect']}, p = {m['p_value']:.4g}",
              f"- Share of reviews with a negative sentiment per aspect (%): {r4['aspect_negative_share_pct']}", ""]
    else:
        L += [r4["note"], ""]
    if comparison is not None:
        L += ["## Model comparison (held-out labelled test set)", _md_table(comparison), ""]
    open(os.path.join(out_dir, "report.md"), "w").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export", required=True)
    ap.add_argument("--participants")
    ap.add_argument("--train-data", help="labelled CSV (text + 5 aspect columns)")
    ap.add_argument("--model", default="tfidf-svm")
    ap.add_argument("--bert-dir", help="saved bert_model.py output to include in the comparison table")
    ap.add_argument("--low-effort-q", type=float, default=0.5)
    ap.add_argument("--synthetic", action="store_true", help="mark report as based on synthetic data")
    ap.add_argument("--out", default="report")
    a = ap.parse_args()
    labelled = load_labelled(a.train_data) if a.train_data else None
    model = get_model(a.model, split(labelled)[0] if labelled is not None and a.model.startswith("tfidf") else labelled)
    res = analyse(load_export(a.export), model, parse_participants(a.participants) if a.participants else None, a.low_effort_q)
    cmp_ = model_comparison(labelled, a.bert_dir) if labelled is not None else None
    write_report(res, cmp_, a.out, a.synthetic)
    print(f"report written to {a.out}/report.md")


if __name__ == "__main__":
    main()
