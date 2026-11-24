"""Creates a FAKE export in the exact backend CSV format, to test the pipeline before real data exists."""
import csv, random, sys
sys.path.insert(0, ".")
from medbook_analysis.synth import make_review
from medbook_analysis.config import ASPECTS

rng = random.Random(7)
HEAD = ("studyId,group,doctorId,submittedAt,overallRating,ratingDoctor,ratingStaff,ratingWaiting,ratingCleanliness,"
        "ratingBilling,freeText,wordCount,aspectsMentioned,detailD,uniquenessU,consistencyC,qualityQ,gatePassed,rewardType,rewardStatus").split(",")
with open("data/demo_export.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(HEAD)
    for g, p in (("A", .22), ("B", .52), ("C", .50), ("D", .55)):
        for i in range(40):
            if rng.random() > p: continue
            r = make_review(rng); text = r["text"] if rng.random() < .8 else rng.choice(["good", "nice doctor", ""])
            neg = sum(r[a] == "negative" for a in ASPECTS); pos = sum(r[a] == "positive" for a in ASPECTS)
            stars = 5 if rng.random() < .3 and neg else max(1, min(5, 3 + pos - neg + rng.choice([0, 1])))   # halo: some positive stars hide a negative aspect
            wc = len(text.split()); q = round(min(1, .3 + wc / 40 + rng.random() * .2), 4)
            w.writerow([f"S{g}{i:03d}", g, 1, "2026-10-20T10:00:00", stars, "", "", "", "", "", text, wc, 0, 0, 1, 1, q, q >= .75, "points", "granted"])
print("wrote data/demo_export.csv")
