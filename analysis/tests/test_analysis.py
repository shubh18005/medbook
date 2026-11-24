"""pytest tests for the analysis package. Run:  cd analysis && python -m pytest -q"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import pandas as pd
import pytest
from medbook_analysis import measures as M, stats_tests as S
from medbook_analysis.annotation import kappa_report
from medbook_analysis.baseline import TfidfAspectModel
from medbook_analysis.config import ASPECTS, overall_label
from medbook_analysis.evaluate import split, aspect_report
from medbook_analysis.pipeline import load_export, analyse
from medbook_analysis.serve import overall_polarity
from medbook_analysis.synth import generate, load_labelled


def asp(rows):
    return pd.DataFrame([{a: r.get(a, "absent") for a in ASPECTS} for r in rows])


def test_overall_label_mapping():
    assert [overall_label(s) for s in (1, 2, 3, 4, 5)] == ["negative", "negative", "neutral", "positive", "positive"]


def test_mixed_and_masked_rates_hand_computed():
    a = asp([{"doctor": "positive", "cleanliness": "negative"},     # mixed, has negative
             {"doctor": "positive"},                                  # only positive
             {"waiting": "negative"},                                 # negative only
             {"staff": "negative", "billing": "positive"}])           # mixed, has negative
    overall = pd.Series(["positive", "positive", "negative", "negative"])
    assert M.mixed_review_rate(a) == pytest.approx(2 / 4)
    # reviews with a negative aspect: #0,#2,#3 ; of those overall positive: only #0  -> 1/3
    assert M.masked_negative_rate(a, overall) == pytest.approx(1 / 3)


def test_missed_negative_rates():
    true = asp([{"doctor": "negative"}, {"staff": "negative"}, {"billing": "positive"}])
    pred = asp([{"doctor": "negative"}, {"staff": "neutral"}, {"billing": "positive"}])
    assert M.missed_negative_rate(true, pred) == pytest.approx(1 / 2)
    assert M.overall_view_missed_rate(true, pd.Series(["negative", "positive", "positive"])) == pytest.approx(1 / 2)


def test_mcnemar_runs_and_counts_discordant():
    a = asp([{"doctor": "negative"}] * 10 + [{"doctor": "positive"}] * 2)
    overall = pd.Series(["positive"] * 10 + ["negative"] * 2)
    r = M.mcnemar_overall_vs_aspect(a, overall)
    assert r["only_aspect"] == 10 and r["only_overall"] == 2 and 0 < r["p_value"] < 0.05


def test_response_rate_matches_paper_table_iv():
    # Paper Table IV: 9/21/20/22 out of 40 -> chi2(3)=11.1, p=0.011
    t = S.response_rate_tests({"A": (9, 40), "B": (21, 40), "C": (20, 40), "D": (22, 40)})
    assert t["chi2"] == pytest.approx(11.1, abs=0.05) and t["p_chi2"] == pytest.approx(0.011, abs=0.001)
    assert all(0 <= p["p_holm"] <= 1 for p in t["pairwise"])


def test_small_counts_use_permutation_test():
    t = S.response_rate_tests({"A": (1, 6), "B": (4, 6), "C": (3, 6), "D": (5, 6)}, n_perm=500)
    assert t["small_expected_counts"] and 0 < t["p_permutation"] <= 1


def test_kruskal_detects_real_difference_and_handles_constant():
    rng = np.random.RandomState(1)
    df = pd.DataFrame({"study_group": np.repeat(list("AB"), 40), "x": np.r_[rng.normal(0, 1, 40), rng.normal(2, 1, 40)]})
    r = S.kruskal_with_posthoc(df, "x")
    assert r["p"] < 0.001 and r["pairwise"][0]["p_holm"] < 0.001 and r["epsilon_sq"] >= 0
    assert "note" in S.kruskal_with_posthoc(df.assign(x=1.0), "x")


def test_kappa_perfect_and_disagreement():
    d = generate(100, seed=3, label_noise=0)
    assert kappa_report(d, d)["kappa"].iloc[-1] == pytest.approx(1.0)
    e = d.copy(); e[ASPECTS] = "neutral"
    assert kappa_report(d, e)["kappa"].iloc[-1] < 0.2
    with pytest.raises(ValueError):
        kappa_report(d, d.iloc[:50])


def test_synthetic_schema_and_loader(tmp_path):
    p = tmp_path / "x.csv"; generate(30).to_csv(p, index=False)
    assert len(load_labelled(str(p))) == 30
    pd.DataFrame({"text": ["a"], "doctor": ["great"]}).to_csv(p, index=False)
    with pytest.raises(ValueError):
        load_labelled(str(p))


@pytest.mark.parametrize("kind", ["lr", "svm"])
def test_tfidf_learns_well_above_chance(kind):
    tr, te = split(generate(800, seed=0))
    m = TfidfAspectModel(kind).fit(tr)
    rep = aspect_report(te, m.predict(te["text"])).set_index("aspect")
    assert rep.loc["MACRO", "f1"] > 0.8


def test_serve_overall_polarity():
    assert overall_polarity({"doctor": "positive", "staff": "positive", "waiting": "negative"}) == 1
    assert overall_polarity({"doctor": "positive", "waiting": "negative"}) == 0
    assert overall_polarity({"doctor": "absent"}) == 0


def test_pipeline_on_backend_format_export(tmp_path):
    csv = tmp_path / "e.csv"
    rows = ["studyId,group,doctorId,submittedAt,overallRating,ratingDoctor,ratingStaff,ratingWaiting,ratingCleanliness,ratingBilling,freeText,wordCount,aspectsMentioned,detailD,uniquenessU,consistencyC,qualityQ,gatePassed,rewardType,rewardStatus"]
    texts = ["the doctor was very good but the clinic was dirty", "'=SUM(1) staff was rude", "good", ""]
    for i, g in enumerate("ABCD" * 6):
        t = texts[i % 4]
        rows.append(f'S{i},{g},1,2026-10-20,{3 + i % 3},,,,,,"{t}",5,1,0.5,1,1,{0.4 + (i % 5) / 10},True,points,granted')
    csv.write_text("\n".join(rows))
    ex = load_export(str(csv))
    assert not ex["free_text"].str.startswith("'").any(), "formula-injection apostrophe must be stripped"
    model = TfidfAspectModel("svm").fit(generate(500, seed=2))
    res = analyse(ex, model, {"A": 10, "B": 10, "C": 10, "D": 10})
    assert res["rq1"]["tests"]["dof"] == 3 and "mixed_review_rate" in res["rq4"]
