# Final run (19 Nov 2026) - what is real, what is simulated

| Part | Data | Status |
|---|---|---|
| Survey (28 Google-Form responses) | REAL | 24 unique texts: one paragraph appears 4x (+1 truncated copy), another 2x - flagged as a data-quality issue |
| Aspect labels for the 28 | REAL text, labelled by ONE annotator (Claude) | **Needs a 2nd annotator** (`data/annotator2_TEMPLATE.csv`, then `python -m medbook_analysis.annotation a1.csv a2.csv`) for Cohen's kappa |
| 87 hand-written reviews | WRITTEN BY HAND for training/testing (English + Hinglish + typos) | not patient data |
| 1500 synthetic reviews | template-generated (old) | only used in the TF-IDF rows |
| Model evaluation (`model_results.md`) | real 28 as test set | clause model was written knowing these texts -> its score is optimistic |
| Gate on real 28 (`real28_gate_*.csv`) | REAL texts, REAL Java classes | valid |
| Pilot (`pilot_export.csv`, `pilot_report/`) | **SIMULATED**: who responds is assumed (A 25%, B 55%, C 60%, D 50%) | tests the pipeline, proves nothing about patients |
| DistilBERT | NOT trained | no torch / no internet in this environment - use Colab (see analysis/README.md step 2) |

Reproduce: `python build_labelled.py && python run_final.py` ; pilot: start `python -m medbook_analysis.serve --model clause --port 8001`, then `python sim/simulate_pilot.py --model-url http://127.0.0.1:8001` and `python -m medbook_analysis.pipeline --export results_final/pilot_export.csv --participants A=40,B=40,C=40,D=40 --train-data data/labelled.csv --model clause --out results_final/pilot_report` (the simulation needs the Java classes compiled into `BACKEND_CLASSES`, see sim/PilotScore.java).
