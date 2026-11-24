#!/usr/bin/env python3
"""
Fills the running MedBook website with study data THROUGH ITS OWN API, exactly like real users would:
  patient registers  ->  books an appointment  ->  doctor marks it completed  ->  (some) patients submit feedback.
Everything then shows up in Admin > Feedback Study (groups A-D, response rate, quality gate, rewards, export).

Standard library only (no pip install).  Backend must be running.

    python tools/seed_study_via_api.py --base http://localhost:8080 --patients 300

WHO RESPONDS is decided by this script from the assumptions below (they are NOT measured on real patients).
The texts are the real survey responses + hand-written reviews (analysis/data/*.csv).
Tell your teacher how this data was produced. Run it once on a fresh database (restart the backend to reset H2).
"""
import argparse, csv, json, os, random, urllib.request, urllib.error
from datetime import date, datetime, timedelta, timezone

RESPONSE_P = {"A": 0.25, "B": 0.55, "C": 0.60, "D": 0.50}      # share of completed visits that get feedback
LOW_EFFORT_P = {"A": 0.15, "B": 0.35, "C": 0.40, "D": 0.15}     # share of responders writing blank / one-word text
OFFER_TO_GROUP = {"none": "A", "points": "B", "discount": "C", "gated": "D"}
LOW = ["good", "nice doctor", "ok", "very good", "", "", "nice", "best", "thanks"]
DOCTORS = [("priya@medbook.in", "doc-1"), ("arjun@medbook.in", "doc-2"), ("sunita@medbook.in", "doc-3"),
           ("vikram@medbook.in", "doc-4"), ("ananya@medbook.in", "doc-5"), ("rohit@medbook.in", "doc-6")]
SLOTS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
FIRST = "Aarav Vivaan Aditya Rohan Karan Rahul Amit Neha Pooja Riya Sneha Anjali Priyanka Kritika Mohit Nikhil Sanjay Ritu Meera Isha Kabir Dev Tanvi Simran Harsh Yash Ayesha Farhan Zoya".split()
LAST = "Sharma Verma Gupta Singh Yadav Mishra Tyagi Chauhan Rastogi Saxena Jain Agarwal Khan Pandey Kumar Joshi Bansal".split()
REASONS = ["Fever and cough", "Routine check-up", "Back pain", "Skin rash", "Chest discomfort", "Headache", "Follow-up visit", "Stomach pain"]
SCORE = {"positive": 5, "neutral": 3, "negative": 1}


def call(base, method, path, body=None, token=None):
    req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode(); return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code} {e.read().decode()[:200]}")


def load_pool(rng, root):
    pool = []
    for f in ("real_survey_labelled.csv", "handwritten_labelled.csv"):
        with open(os.path.join(root, "analysis", "data", f), encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                pos = sum(row[a] == "positive" for a in ("doctor", "staff", "waiting", "cleanliness", "billing"))
                neg = sum(row[a] == "negative" for a in ("doctor", "staff", "waiting", "cleanliness", "billing"))
                stars = max(1, min(5, 3 + pos - neg + rng.choice([0, 0, 1])))
                if neg and rng.random() < 0.3: stars = 5            # 'halo' stars: positive rating hiding a negative aspect
                pool.append((stars, row))
    seen, uniq = set(), []
    for s, r in pool:
        if r["text"] not in seen: seen.add(r["text"]); uniq.append((s, r))
    rng.shuffle(uniq); return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8080"); ap.add_argument("--patients", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42); a = ap.parse_args()
    rng = random.Random(a.seed); root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    pool = load_pool(rng, root)
    doc_tokens = {did: call(a.base, "POST", "/api/auth/login", {"role": "doctor", "email": em, "password": "doc123"})["token"] for em, did in DOCTORS}
    used, stats = set(), {g: {"patients": 0, "responded": 0} for g in "ABCD"}
    start = date.today() - timedelta(days=20)
    for i in range(a.patients):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        email = f"{name.lower().replace(' ', '.')}{rng.randint(10, 9999)}@gmail.com"
        reg = call(a.base, "POST", "/api/auth/register/patient", {"name": name, "email": email, "password": "patient123",
                   "phone": f"+91 9{rng.randint(100000000, 999999999)}", "age": rng.randint(18, 70), "gender": rng.choice(["Male", "Female"])})
        tok = reg["token"]
        did = DOCTORS[i % len(DOCTORS)][1]
        while True:                                                       # find a free doctor/date/time slot
            d, t = (start + timedelta(days=rng.randint(0, 19))).isoformat(), rng.choice(SLOTS)
            if (did, d, t) not in used: used.add((did, d, t)); break
        apt = call(a.base, "POST", "/api/appointments", {"doctorId": did, "date": d, "time": t, "reason": rng.choice(REASONS), "paymentMode": "pay_at_clinic"}, tok)
        call(a.base, "PATCH", f"/api/appointments/{apt['id']}", {"status": "completed", "diagnosis": "Consultation done",
             "prescription": "As advised", "completedAt": datetime.now(timezone.utc).isoformat()}, doc_tokens[did])
        status = call(a.base, "GET", "/api/feedback/status", None, tok)
        g = OFFER_TO_GROUP[status["offer"]]; stats[g]["patients"] += 1
        if rng.random() > RESPONSE_P[g]: continue
        body = {"appointmentId": apt["id"], "consent": True}
        if rng.random() < LOW_EFFORT_P[g] or not pool:
            body.update(overallRating=rng.choice([3, 4, 5, 5]), freeText=rng.choice(LOW))
        else:
            stars, row = pool.pop(); body.update(overallRating=stars, freeText=row["text"])
            for key, field in (("doctor", "ratingDoctor"), ("staff", "ratingStaff"), ("waiting", "ratingWaiting"),
                               ("cleanliness", "ratingCleanliness"), ("billing", "ratingBilling")):
                if row[key] != "absent" and rng.random() < 0.7:
                    base = SCORE[row[key]]; body[field] = max(1, min(5, base + (rng.choice([0, 0, -1]) if base == 5 else rng.choice([0, 1]) if base == 1 else 0)))
        call(a.base, "POST", "/api/feedback", body, tok); stats[g]["responded"] += 1
    print("group  patients  responded  rate")
    for g, s in stats.items(): print(f"  {g}     {s['patients']:4d}      {s['responded']:4d}    {100 * s['responded'] / max(1, s['patients']):.0f}%")
    print("Now log in as admin (admin@medbook.in / admin123) -> Feedback Study.")


if __name__ == "__main__":
    main()
