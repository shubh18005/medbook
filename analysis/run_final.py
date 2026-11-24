"""
Final model evaluation on REAL + hand-written labelled data.

 Setting A  train SYNTHETIC only            -> test on the 28 REAL responses   (domain-gap check)
 Setting B  train SYNTHETIC + HAND-WRITTEN  -> test on the 28 REAL responses   (headline number: real text never seen in training)
 Setting C  repeated 5-fold CV over REAL + HAND-WRITTEN (+ synthetic in every training fold)
Baselines: always-'absent' majority classifier, and the keyword/lexicon view the Java backend uses (aspect detection only).
Writes results_final/model_results.json and model_results.md
"""
import json, os, sys, warnings
import numpy as np, pandas as pd
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score
warnings.filterwarnings("ignore")
from medbook_analysis.config import ASPECTS
from medbook_analysis.baseline import TfidfAspectModel
from medbook_analysis.evaluate import aspect_report
from medbook_analysis.clause_model import ClauseAspectModel
from medbook_analysis import measures as M

OUT = "results_final"; os.makedirs(OUT, exist_ok=True)
syn = pd.read_csv("data/synthetic_labelled.csv")
real = pd.read_csv("data/real_survey_labelled.csv")
hand = pd.read_csv("data/handwritten_labelled.csv")
real_u = real.drop_duplicates("text").reset_index(drop=True)   # de-duplicated real set (24 unique texts)

def score(model, test):
    pred = model.predict(test["text"]); rep = aspect_report(test, pred).set_index("aspect")
    return pred, {"macro_f1_4class": rep.loc["MACRO","f1"], "macro_f1_polarity": rep.loc["MACRO","f1_polarity_mentioned"],
                  "missed_negative_pct": 100*M.missed_negative_rate(test, pred)}
def acc(test, pred):  # exact-match accuracy over all 5 aspects x reviews
    return float(np.mean([(test[a].values == pred[a].values).mean() for a in ASPECTS]))

res = {"n_real": len(real), "n_real_unique": len(real_u), "n_hand": len(hand), "n_syn": len(syn)}
rows = []
for kind, name in (("lr","TF-IDF + LR"),("svm","TF-IDF + SVM")):
    for setting, tr in (("A: synthetic only", syn), ("B: synthetic + handwritten", pd.concat([syn, hand]))):
        for tname, te in (("real28", real), ("real24_unique", real_u)):
            m = TfidfAspectModel(kind).fit(tr); p, s = score(m, te)
            rows.append({"model": name, "train": setting, "test": tname, "accuracy": acc(te, p), **s})
cm = ClauseAspectModel()
for tname, te in (("real28", real), ("real24_unique", real_u), ("handwritten87", hand)):
    p_, s_ = score(cm, te)
    rows.append({"model": "Clause rules (hybrid)", "train": "none (rule-based)", "test": tname, "accuracy": acc(te, p_), **s_})
# majority baseline: predict 'absent' for every aspect
maj = pd.DataFrame({a: ["absent"]*len(real) for a in ASPECTS})
rows.append({"model": "Majority ('absent')", "train": "-", "test": "real28", "accuracy": acc(real, maj),
             "macro_f1_4class": aspect_report(real, maj).set_index("aspect").loc["MACRO","f1"], "macro_f1_polarity": float("nan"),
             "missed_negative_pct": 100*M.missed_negative_rate(real, maj)})
# C: repeated CV
cv = {k: [] for k in ("lr","svm")}
real_hand = pd.concat([real_u, hand]).reset_index(drop=True)
for seed in range(3):
    for tr_i, te_i in KFold(5, shuffle=True, random_state=seed).split(real_hand):
        tr = pd.concat([syn, real_hand.iloc[tr_i]]); te = real_hand.iloc[te_i].reset_index(drop=True)
        for k in cv:
            m = TfidfAspectModel(k).fit(tr); p, s = score(m, te); cv[k].append({**s, "accuracy": acc(te, p)})
for k, nm in (("lr","TF-IDF + LR"),("svm","TF-IDF + SVM")):
    d = pd.DataFrame(cv[k]); rows.append({"model": nm, "train": "C: 3x5-fold CV (real24+hand87, +synthetic)", "test": "held-out folds",
        **{c: d[c].mean() for c in d.columns}, "cv_sd_macro_f1_polarity": d["macro_f1_polarity"].std()})
tab = pd.DataFrame(rows); res["table"] = tab.round(3).to_dict("records")

# per-aspect report for the headline model on real28
m = ClauseAspectModel(); p, _ = score(m, real)
res["per_aspect_headline"] = aspect_report(real, p).round(3).to_dict("records")
# RQ4 on the REAL data: gold labels vs model predictions
stars = pd.read_csv("data/real_survey_clean.csv")["stars"]
ov = M.overall_labels(stars)
res["rq4_real"] = {"n": len(real),
  "gold": {"MR": M.mixed_review_rate(real), "MNR": M.masked_negative_rate(real, ov),
           "n_with_negative_aspect": int((real[ASPECTS]=="negative").any(axis=1).sum())},
  "model_clause_rules": {"MR": M.mixed_review_rate(p), "MNR": M.masked_negative_rate(p, ov)}}
# same on the de-duplicated 24
ru_idx = real.drop_duplicates("text").index; ru = real.loc[ru_idx].reset_index(drop=True)
res["rq4_real"]["gold_unique24"] = {"n": len(ru), "MR": M.mixed_review_rate(ru), "MNR": M.masked_negative_rate(ru, ov.loc[ru_idx].reset_index(drop=True))}
res["rq4_real"]["mcnemar_gold"] = M.mcnemar_overall_vs_aspect(real, ov)
json.dump(res, open(f"{OUT}/model_results.json","w"), indent=2, default=float)
with open(f"{OUT}/model_results.md","w") as f:
    f.write(tab.round(3).to_markdown(index=False) + "\n\nPer-aspect (clause rules, test real28):\n\n"
            + aspect_report(real, p).round(3).to_markdown(index=False) + "\n\nRQ4 on real data:\n\n```\n" + json.dumps(res["rq4_real"], indent=1, default=float) + "\n```\n")
print(open(f"{OUT}/model_results.md").read())
