import pandas as pd
from medbook_analysis.clause_model import ClauseAspectModel, predict_one
from medbook_analysis.evaluate import aspect_report
from medbook_analysis.pipeline import get_model
from medbook_analysis._compat import mcnemar, multipletests_holm, wilson


def test_mixed_review_is_split_by_clause():
    r = predict_one("The doctor was great but the waiting time was very long and billing was confusing")
    assert r["doctor"] == "positive" and r["waiting"] == "negative" and r["billing"] == "negative"
    assert r["cleanliness"] == "absent"


def test_negation_flips_polarity():
    assert predict_one("the clinic was not clean")["cleanliness"] == "negative"
    assert predict_one("I did not have to wait for a long time")["waiting"] == "positive"
    assert predict_one("koi billing issue nahi tha")["billing"] == "positive"


def test_hinglish_cues():
    r = predict_one("Doctor bahut ache the lekin bheed bahut thi aur safai nahi thi")
    assert r["doctor"] == "positive" and r["waiting"] == "negative"


def test_no_aspect_means_absent():
    assert set(predict_one("It was good").values()) == {"absent"}
    assert set(predict_one("").values()) == {"absent"}


def test_clause_model_beats_tfidf_on_real_labelled_data():
    d = pd.read_csv("data/real_survey_labelled.csv")
    f = aspect_report(d, ClauseAspectModel().predict(d["text"])).set_index("aspect").loc["MACRO", "f1_polarity_mentioned"]
    assert f > 0.5


def test_pipeline_accepts_clause_spec():
    assert isinstance(get_model("clause", None), ClauseAspectModel)


def test_compat_stats_match_known_values():
    assert abs(mcnemar([[5, 2], [9, 0]]).pvalue - 0.0654296875) < 1e-9
    assert list(multipletests_holm([0.01, 0.04, 0.03]).round(3)) == [0.03, 0.06, 0.06]
    lo, hi = wilson(5, 20)
    assert abs(lo - 0.1119) < 1e-3 and abs(hi - 0.4687) < 1e-3
