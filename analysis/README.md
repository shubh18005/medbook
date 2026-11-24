# MedBook analysis pipeline (Python)

Implements the "analysis layer" of the synopsis (Sections 5.2.4, 5.3, 6.3) and research paper (Sections IV-E, IV-F, V).

```
analysis/
  medbook_analysis/
    config.py       aspects, labels, star-rating -> overall label
    synth.py        SYNTHETIC labelled-data generator + loader/validator for the real labelled CSV
    baseline.py     TF-IDF + Logistic Regression / linear SVM, one classifier per aspect
    bert_model.py   DistilBERT/BERT with 5 aspect heads (fine-tuning, predict, save/load, offline smoke test)
    evaluate.py     per-aspect precision / recall / F1, latency per review, train/test split
    measures.py     mixed-review rate (MR), masked-negative rate (MNR), McNemar (overall vs aspect view)
    stats_tests.py  chi-square / permutation / Fisher+Holm, Kruskal-Wallis + pairwise MWU+Holm, effect sizes, Wilson CIs
    annotation.py   Cohen's kappa between two annotators
    pipeline.py     backend CSV export -> RQ1..RQ4 report (report.md + results.json) + model comparison table
    serve.py        local HTTP service so the Spring Boot backend can use the trained model
  tests/            pytest suite
  demo_export.py    makes a FAKE export in the backend's CSV format (to test the pipeline)
  data/             synthetic_labelled.csv (synthetic!) and demo_export.csv (fake!)
```

## Quick start
```bash
cd analysis
pip install -r requirements.txt
python -m pytest -q                                   # 13 tests

python -m medbook_analysis.synth --n 1500 --out data/synthetic_labelled.csv   # SYNTHETIC data
python demo_export.py                                 # FAKE export, only to see the pipeline run
python -m medbook_analysis.pipeline --export data/demo_export.csv --participants A=40,B=40,C=40,D=40 \
       --train-data data/synthetic_labelled.csv --model tfidf-svm --synthetic --out report_demo
```

## With real data (what you must do for the final results)
1. **Label real text.** Collect public hospital reviews + the study's free-text responses. Two people label them in the CSV
   format `text,doctor,staff,waiting,cleanliness,billing` (each aspect: `absent|negative|neutral|positive`).
   Check agreement: `python -m medbook_analysis.annotation annotator1.csv annotator2.csv`.
   Merge into `data/labelled.csv`.
2. **Train DistilBERT** (needs internet + preferably a GPU / Colab):
   `python -m medbook_analysis.bert_model train --data data/labelled.csv --out models/distilbert`
3. **Run the study** in MedBook, then download the CSV from the admin *Feedback Study* tab.
4. **Analyse:** `python -m medbook_analysis.pipeline --export medbook-feedback-export.csv --participants A=..,B=..,C=..,D=.. --train-data data/labelled.csv --model bert:models/distilbert --bert-dir models/distilbert --out report`
5. **Use the model inside the quality gate (optional):** run `python -m medbook_analysis.serve --model bert:models/distilbert`
   and set `study.sentiment.model-url=http://127.0.0.1:8001` in `backend/src/main/resources/application.properties`.
   If the service is down, the backend silently falls back to the built-in word list.

## Honest notes
* Everything in `data/` is synthetic/fake. Scores on it are optimistic and are not evidence about real patients.
* `absent` is an extra label (aspect not mentioned) on top of the paper's three polarities, because real reviews rarely mention all five aspects. `f1_polarity_mentioned` reports F1 over the three polarities on mentioned aspects only.
* Overall label from stars: 4-5 positive, 3 neutral, 1-2 negative (`config.overall_label`).
* The export has only people who responded, so RQ1 needs the participant counts per group (`--participants`).
* For small counts, RQ1 adds a Monte-Carlo permutation p-value (scipy has no exact r x 2 test).
* Post-hoc for Kruskal-Wallis is pairwise Mann-Whitney with Holm correction (not Dunn's test).

## Final run (Session 12)
`python build_labelled.py && python run_final.py` -> `results_final/model_results.md`. A rule/lexicon model that works with no training
data is available as `--model clause` (`python -m medbook_analysis.serve --model clause --port 8001`, then set
`study.sentiment.model-url=http://127.0.0.1:8001`). See `results_final/README.md` for what is real vs simulated.
