"""
SIMULATED pilot of the MedBook feedback study (groups A-D), to test the whole pipeline end to end.

!! Everything about WHO responds is an ASSUMPTION, not a finding. The only real material is the text/rating of the
!! 28 survey responses (re-used as 'what a patient might write'); handwritten reviews fill the rest.
Scoring uses the real Java backend classes (QualityScorer, SentimentLexicon, RewardService).
Usage: python sim/simulate_pilot.py [--n 40] [--theta 0.75] [--seed 11] [--model-url http://127.0.0.1:8001] [--out results_final/pilot_export.csv]
"""
import argparse, os, random, subprocess, sys
sys.path.insert(0, ".")
import pandas as pd
from medbook_analysis.config import ASPECTS

ASSUMED_RESPONSE_P = {"A": 0.25, "B": 0.55, "C": 0.60, "D": 0.50}   # share of patients with a completed visit who respond
ASSUMED_LOWEFFORT_P = {"A": 0.15, "B": 0.35, "C": 0.40, "D": 0.15}  # share of responders who write a blank / one-word text
LOW = ["good", "nice doctor", "ok", "very good", "", "", "nice", "best", "thanks"]

def stars_from_labels(row, rng):
    pos = sum(row[a] == "positive" for a in ASPECTS); neg = sum(row[a] == "negative" for a in ASPECTS)
    s = 3 + pos - neg + rng.choice([0, 0, 1])
    if neg and rng.random() < 0.3: s = 5            # halo: some positive stars hide a negative aspect
    return max(1, min(5, s))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=40); ap.add_argument("--theta", default="0.75")
    ap.add_argument("--seed", type=int, default=11); ap.add_argument("--model-url", default="")
    ap.add_argument("--out", default="results_final/pilot_export.csv"); a = ap.parse_args()
    rng = random.Random(a.seed)
    stars = pd.read_csv("data/real_survey_clean.csv")
    real = [(int(r.stars), r.text) for r in stars.drop_duplicates("text").itertuples()]
    hand = pd.read_csv("data/handwritten_labelled.csv")
    pool = real + [(stars_from_labels(row, rng), row["text"]) for _, row in hand.iterrows()]
    rng.shuffle(pool)
    rows, counts = [], {}
    for g in "ABCD":
        counts[g] = a.n
        for i in range(a.n):
            if rng.random() > ASSUMED_RESPONSE_P[g]: continue
            if rng.random() < ASSUMED_LOWEFFORT_P[g] or not pool:
                text, st = rng.choice(LOW), rng.choice([4, 5, 5, 3])
            else:
                st, text = pool.pop()
            rows.append(f"S{g}{i:03d}\t{g}\t{st}\t{text}")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    tsv = a.out.replace(".csv", "_input.tsv"); open(tsv, "w").write("\n".join(rows) + "\n")
    cp = os.environ.get("BACKEND_CLASSES", "/home/claude/work/jtest/out_sim")
    subprocess.run(["java", "-cp", cp, "PilotScore", tsv, a.out, a.theta, a.model_url], check=True)
    print("participants:", ",".join(f"{g}={n}" for g, n in counts.items()), "| responders:", len(rows))

if __name__ == "__main__":
    main()
