"""
TF-IDF + Logistic Regression / linear SVM baseline (synopsis Section 5.2.4 (a)).

One classifier per aspect, each predicting {absent, negative, neutral, positive}.
Features: word 1-2-grams + character 3-5-grams (char n-grams make it robust to the typos
real patients make). Negations such as 'not clean' are captured by the bigrams.
"""
from __future__ import annotations
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from .config import ASPECTS


def _features():
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
    ])


def _clf(kind: str):
    if kind == "lr":
        return LogisticRegression(max_iter=2000, C=5.0)
    if kind == "svm":
        return LinearSVC(C=1.0)
    raise ValueError("kind must be 'lr' or 'svm'")


class TfidfAspectModel:
    def __init__(self, kind: str = "lr"):
        self.kind = kind
        self.pipes = {a: Pipeline([("f", _features()), ("c", _clf(kind))]) for a in ASPECTS}

    def fit(self, df: pd.DataFrame):
        for a in ASPECTS:
            self.pipes[a].fit(df["text"], df[a])
        return self

    def predict(self, texts) -> pd.DataFrame:
        texts = list(texts)
        return pd.DataFrame({a: self.pipes[a].predict(texts) for a in ASPECTS})

    def save(self, path: str):
        joblib.dump(self, path)

    @staticmethod
    def load(path: str) -> "TfidfAspectModel":
        return joblib.load(path)
