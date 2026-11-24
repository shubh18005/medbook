# MedBook — An Intelligent Patient Feedback System Integrated with Healthcare



MedBook is a full-stack clinic appointment platform (React + Java/Spring Boot) extended with a **research module** that studies how rewards change patient feedback. After a doctor completes a consultation, the patient gets a one-minute feedback form; a reward engine applies one of four study conditions; an automatic **quality gate** decides whether a gated reward is paid; and the free text is analysed at **aspect level** (doctor, staff, waiting time, cleanliness, billing).

B.Tech (CSE) final-year project, Ajay Kumar Garg Engineering College, Ghaziabad (AKTU), session 2023–2027.


---

## Features

| Role | What it can do |
|---|---|
| **Patient** | Search doctors by specialty/city, book on an availability calendar, see a privacy-preserving live queue estimate, submit feedback after a completed visit |
| **Doctor** | Confirm/decline requests, record diagnosis and prescription to close a visit, manage schedule and fee |
| **Admin** | Approve doctor registrations, browse directories, and open the **Feedback Study** tab (groups A–D, response rates, quality-gate results, rewards, anonymised CSV export) |

**Study module**

| Group | Rule |
|---|---|
| A | No reward (control) |
| B | 50 points on every submission |
| C | 10 % discount on every submission |
| D | 50 points only if the quality score `Q ≥ 0.75` |

Quality score: `Q = 0.4·D + 0.3·U + 0.3·C` — detail (length, aspects mentioned), uniqueness (not a copy of earlier texts) and rating–text consistency.

## Tech stack

- **Frontend:** React 19, Vite
- **Backend:** Java 17, Spring Boot 3, Spring Security (JWT, BCrypt), JPA, H2
- **Analysis:** Python (pandas, scikit-learn, SciPy, statsmodels)

## Repository layout

```
backend/    Spring Boot REST API (port 4001)
frontend/   React + Vite client (port 5173)
analysis/   Python package: models, measures, statistics, pipeline, model service
tools/      seed_study_via_api.py  (fills the running site with study data via its own API)
logbook.md  Development log (sessions 1–12)
```

## Quick start (local)

Requirements: Java 17+, Maven, Node 18+, Python 3.10+.

```bash
# 1) Optional but recommended: aspect-model service (backend falls back to a word list without it)
cd analysis
python -m venv .venv                 # .venv is ignored by git
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m medbook_analysis.serve --model clause --port 8001

# 2) Backend  (new terminal)
cd backend
mvn spring-boot:run                  # http://localhost:4001

# 3) Frontend (new terminal)
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

To use the model service, set `study.sentiment.model-url=http://127.0.0.1:8001` in `backend/src/main/resources/application.properties`.

### Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@medbook.in | admin123 |
| Doctor | priya@medbook.in | doc123 |
| Patient | rahul@gmail.com | patient123 |

These are demo credentials for local use. Change `jwt.secret` (or set the `JWT_SECRET` environment variable) before hosting anywhere public.

### Fill the study with data (optional)

With the backend running **on a fresh database** (delete `backend/data/` first), this registers patients through the real API, completes their visits and submits feedback for a share of them:

```bash
python tools/seed_study_via_api.py --base http://localhost:4001 --patients 300
```

> **Important:** the response behaviour in this script (who responds, who writes low-effort text) is *assumed*, not measured. Data created this way validates the system; it is not evidence about real patients. Run it only once per database.

## Analysis and results

```bash
cd analysis
python build_labelled.py && python run_final.py                    # model comparison, RQ4 on real survey
python -m medbook_analysis.pipeline --export <exported.csv> --participants A=75,B=75,C=75,D=75 \
       --train-data data/labelled.csv --model clause --out results_final/report
pytest                                                             # analysis tests
cd ../backend && mvn test                                          # backend tests
```

Summary (details in `analysis/results_final/`):

- **Real data (28 survey responses, 24 unique texts):** 10 of the 15 reviews that contain a negative aspect (66.7 %) had a 4–5 star rating; the aspect view detects all 15, the star view 3 (exact McNemar p < 0.001). Waiting time and billing are the main hidden problems.
- **Models on the real reviews:** TF–IDF + SVM polarity macro-F1 0.33; clause-level rule model 0.67 (optimistic — rules were written after reading the texts).
- **Quality gate on real reviews (θ = 0.75):** 16 of 28 pass; repeated copies, one-word texts and a rating–text contradiction are rejected.
- **RQ1–RQ3 (rewards):** validated only with *simulated* participants; no real volunteer study yet, so no claim about the effect of rewards is made.
- **Not done:** DistilBERT/BERT fine-tuning, second annotator (Cohen's κ), real volunteer study.



## Team

| Name | Main area |
|---|---|
| Shubh Garg | Literature review, front end |
| Shubham Yadav | Spring Boot back end, feedback API |
| Shashank Dubey | Aspect models and statistical analysis |
| Samyak Srivastava | Survey, data labelling, documentation |


## Limitations

Small real sample from a college community; single annotator; simulated rewards and participants for RQ1–RQ3; single platform. See the project report for the full list.
