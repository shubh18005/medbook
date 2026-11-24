"""
Synthetic labelled-data generator.

IMPORTANT: this produces TEMPLATE-GENERATED text. It exists so the pipeline can be
developed and tested end to end before real annotated data exists. Scores obtained on
it are optimistic and must NOT be reported as evidence about real patients (the research
paper says the same about Tables IV/V). Replace it with real labelled data in the same
CSV format (see load_labelled) for the final results.

Labelled CSV format: columns  text, doctor, staff, waiting, cleanliness, billing
each aspect column in {absent, negative, neutral, positive}.
"""
from __future__ import annotations
import random
import pandas as pd
from .config import ASPECTS

# phrases[aspect][polarity] -> list of clauses. Includes negation and neutral wording
# so a pure keyword rule is not enough.
P = {
    "doctor": {
        "positive": ["the doctor was very good", "doctor listened to me carefully", "the doctor explained everything clearly",
                     "the doctor was caring and thorough", "doctor was not rushed and answered all my questions",
                     "doctor was friendly and professional"],
        "neutral": ["the doctor was okay", "doctor was average", "consultation with the doctor was fine",
                    "the doctor was neither good nor bad", "doctor did the usual checkup"],
        "negative": ["the doctor was dismissive", "doctor did not listen to me", "the doctor was rude",
                     "doctor was careless and rushed", "the doctor did not explain the medicine",
                     "doctor was not helpful at all"],
    },
    "staff": {
        "positive": ["the staff was polite and helpful", "front desk was very courteous", "staff were friendly",
                     "reception staff was not rude and helped me quickly", "the attendants were supportive"],
        "neutral": ["the staff was okay", "reception was average", "staff behaviour was normal",
                    "staff did their job"],
        "negative": ["the staff was rude", "reception staff was unhelpful", "staff ignored me at the counter",
                     "the front desk was not polite", "staff behaviour was unprofessional"],
    },
    "waiting": {
        "positive": ["there was no delay at all", "waiting time was short", "the queue moved quickly",
                     "i was seen on time", "the wait was not long"],
        "neutral": ["waiting time was average", "i waited for some time", "the wait was normal",
                    "waiting time was okay"],
        "negative": ["the waiting time was very long", "there was a big delay", "i waited for hours",
                     "the queue was slow and crowded", "the wait was not short at all"],
    },
    "cleanliness": {
        "positive": ["the clinic was clean", "the waiting area was spotless", "hygiene was excellent",
                     "washrooms were not dirty and well kept", "the room was tidy"],
        "neutral": ["cleanliness was okay", "the clinic was average in hygiene", "cleanliness was normal"],
        "negative": ["the clinic was dirty", "washrooms were filthy", "the room was not clean",
                     "hygiene was poor", "the waiting area was messy and smelly"],
    },
    "billing": {
        "positive": ["billing was transparent", "the charges were reasonable", "the bill was clear",
                     "fees were not expensive", "payment was smooth"],
        "neutral": ["billing was okay", "the charges were average", "fees were normal"],
        "negative": ["billing was confusing", "the fees were overpriced", "there were hidden charges",
                     "i was overcharged", "the bill was not clear"],
    },
}
CONNECT = [" and ", ", ", ". ", " but ", ", also ", ". overall "]
OPENERS = ["", "", "", "i visited last week. ", "honest feedback: ", "my experience: "]


def _maybe_typo(s: str, rng: random.Random, p: float = 0.03) -> str:
    out = []
    for ch in s:
        if ch.isalpha() and rng.random() < p:
            r = rng.random()
            if r < 0.4:
                continue            # drop a letter
            if r < 0.7:
                out.append(ch + ch)  # double a letter
                continue
        out.append(ch)
    return "".join(out)


def make_review(rng: random.Random, label_noise: float = 0.03) -> dict:
    k = rng.choices([1, 2, 3, 4, 5], weights=[2, 4, 4, 2, 1])[0]
    chosen = rng.sample(ASPECTS, k)
    clauses, labels = [], {a: "absent" for a in ASPECTS}
    for a in chosen:
        pol = rng.choices(["positive", "neutral", "negative"], weights=[4, 2, 3])[0]
        clauses.append(rng.choice(P[a][pol]))
        labels[a] = pol
    rng.shuffle(clauses)
    text = rng.choice(OPENERS)
    for i, c in enumerate(clauses):
        text += (rng.choice(CONNECT) if i else "") + c
    text = _maybe_typo(text, rng)
    # annotation noise: flip a few labels to a neighbouring label (simulates annotator error)
    for a in ASPECTS:
        if labels[a] != "absent" and rng.random() < label_noise:
            labels[a] = rng.choice([l for l in ["negative", "neutral", "positive"] if l != labels[a]])
    return {"text": text, **labels}


def generate(n: int = 1500, seed: int = 42, label_noise: float = 0.03) -> pd.DataFrame:
    rng = random.Random(seed)
    return pd.DataFrame([make_review(rng, label_noise) for _ in range(n)])


def load_labelled(path: str) -> pd.DataFrame:
    """Load a labelled CSV (real or synthetic) and validate the schema."""
    df = pd.read_csv(path)
    need = ["text"] + ASPECTS
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"Labelled CSV is missing columns: {missing}")
    bad = set(df[ASPECTS].stack().unique()) - {"absent", "negative", "neutral", "positive"}
    if bad:
        raise ValueError(f"Unknown labels in CSV: {bad}")
    df["text"] = df["text"].fillna("").astype(str)
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate SYNTHETIC labelled reviews.")
    ap.add_argument("--n", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/synthetic_labelled.csv")
    a = ap.parse_args()
    df = generate(a.n, a.seed)
    df.to_csv(a.out, index=False)
    print(f"wrote {len(df)} SYNTHETIC rows -> {a.out}")
    print(df.head(5).to_string())
