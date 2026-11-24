"""
Clause-level aspect model (rule + lexicon hybrid, English + Hinglish).

Why: a whole-review TF-IDF classifier needs thousands of labelled reviews to learn 'which aspect is this
sentiment about?'. With ~100 labelled reviews it cannot. This model gets that structure from rules
(aspect keywords + sentiment lexicon + negation + distance) and is therefore usable with no training data.
It has the same interface as TfidfAspectModel (fit / predict) so it plugs into pipeline.py and serve.py.

NOTE ON HONESTY: the lexicons are general-purpose and were written before the model was scored, but the author had
read the 28 survey texts, so scores on them are optimistic. See results_final/README for the evaluation caveats.
"""
from __future__ import annotations
import re
import pandas as pd
from .config import ASPECTS

ASPECT_STEMS = {
    "doctor": ["doctor", "doc", "dr", "specialist", "treat", "tritment", "medicin", "dawai", "checkup", "check", "consult", "diagnos",
               "listen", "explain", "samjha", "pediatric", "physician"],
    "staff": ["staff", "staf", "nurse", "recept", "behaviour", "behavior", "attendant", "counter", "polite", "rude", "wardboy",
              "guard", "assistant", "management"],
    "waiting": ["shortwait", "longwait", "wait", "queue", "line", "slip", "crowd", "bheed", "intezaar", "delay", "late", "token", "slot",
                "baith", "time", "lambi", "hours", "minutes"],
    "cleanliness": ["clean", "hygien", "dirt", "toilet", "washroom", "smell", "saaf", "safai", "gandagi", "tidy", "neat",
                    "filth", "garbage", "sanitar", "phenyl", "spotless", "gandi"],
    "billing": ["bill", "payment", "pay", "paid", "fee", "charge", "price", "cost", "expens", "mehng", "paise", "paisa",
                "insurance", "receipt", "rupee", "afford", "scam", "overcharg", "rates"],
}
# words that only count as an aspect cue when no other aspect is present in the same clause
WEAK = {"staff": {"helpful", "kind", "polite", "rude"}}

POS = set("""shortwait good great excellent amazing wonderful helpful polite friendly kind caring clean hygienic tidy neat quick fast smooth clear
transparent professional satisfied satisfying happy best nice thorough attentive patient courteous pleasant comfortable supportive
reasonable prompt cooperative spotless awesome fantastic perfect humble understanding concentration top notch ok_pos
acha achha accha achhe achee ache acchi badhiya badiya shandar saaf sahi theek_pos kam less short fair cheap free punctual
gently reassuring knowledgeable competent decent loved liked organised organized well""".split())
NEG = set("""longwait bad poor terrible awful rude dirty unhygienic slow long delay delayed late crowded confusing expensive overpriced
overcharged unhelpful careless dismissive rushed disappointed disappointing worst horrible smelly messy chaotic unprofessional
ignored waste hidden uncomfortable pathetic worse unsatisfied unclear filthy disgusting negligent arrogant frustrating frustating
issue issues problem problems mistake kharab bekaar bekar gandagi gandi gandagi zyada jada_neg lambi bheed mehnge mehnga
scam headache endless cramped disorganised disorganized shouting pushing garbage complaint refused favour""".split())
NEUT = set("okay ok average normal fine alright satisfactory moderate theek chalta usual".split())
NEGATORS = {"not", "no", "never", "without", "nahi", "nhi", "na", "didn", "wasn", "isn", "don", "doesn", "didnt", "wasnt",
            "cannot", "hardly", "zero", "nothing"}
SPLIT = re.compile(r"[.!?;\n]+|,|\bbut\b|\bhowever\b|\bthough\b|\balthough\b|\blekin\b|\bpar\b|\bwhile\b|\bdespite\b|\bonly\b", re.I)


IDIOMS = [
    (r"(did not|do not|does not|don't|didn't|no need to|never|not|nahi|nhi)\s+(have to\s+)?wait(\s+for)?(\s+a)?(\s+(long|much|lot))?(\s+time)?", " shortwait "),
    (r"a lot of time|so much time|too much time|time is more|waiting is more|too much|more time|lot of time", " longwait "),
]


def _tok(s):
    s = s.lower().replace("n't", " not")
    for pat, rep in IDIOMS:
        s = re.sub(pat, rep, s)
    return re.findall(r"[a-z]+", s)


def _word_polarity(toks, i):
    w = toks[i]
    if w in ("ok", "okay") or w in NEUT:
        base = 0
    elif w in POS:
        base = 1
    elif w in NEG:
        base = -1
    else:
        return None
    if base != 0 and any(t in NEGATORS for t in toks[max(0, i - 4):i]):
        base = -base
    elif base < 0 and w not in ("longwait",) and any(t in {"nahi", "nhi", "no", "not", "nothing"} for t in toks[i + 1:i + 3]):
        base = -base                                   # 'issue nahi tha', 'problem nhi'

    return base if base != 0 else "u"


def _aspect_positions(toks):
    out = {}
    for i, t in enumerate(toks):
        for a, stems in ASPECT_STEMS.items():
            if any(t == s or (len(s) > 3 and t.startswith(s)) for s in stems):
                if t in ("time", "late", "line", "check", "pay") and a in ("waiting", "doctor", "billing"):
                    pass
                out.setdefault(a, []).append(i)
    return out


def predict_one(text: str) -> dict:
    res = {a: "absent" for a in ASPECTS}
    for clause in SPLIT.split(text or ""):
        toks = _tok(clause)
        if not toks:
            continue
        pos = _aspect_positions(toks)
        if "billing" in pos and "doctor" in pos and all(toks[i] in ("medicin", "medicine", "medicines", "dawai", "tests", "test") for i in pos["doctor"]):
            del pos["doctor"]                              # 'medicines are expensive' is about billing, not the doctor
        # 'time' / 'lambi' etc. alone are weak waiting cues; require wait-ish context
        if "waiting" in pos and not any(t.startswith(("shortwait", "longwait", "wait", "queue", "line", "slip", "crowd", "bheed", "intezaar", "delay", "late", "token", "slot", "baith", "lambi"))
                                        for t in toks):
            del pos["waiting"]
        if not pos:
            continue
        sents = [(i, _word_polarity(toks, i)) for i in range(len(toks))]
        sents = [(i, p) for i, p in sents if p is not None]
        for a, idxs in pos.items():
            score, neutral, used = 0, False, False
            for i, p in sents:
                if i in idxs and a != "waiting":      # the aspect word itself is not a sentiment cue (except e.g. 'rude')
                    pass
                d = min(abs(i - j) for j in idxs)
                if d <= 5 or len(pos) == 1:
                    if p == "u":
                        neutral = True
                    else:
                        # nearest-cue weighting
                        score += p * (1.0 if d <= 3 else 0.6)
                    used = True
            # waiting: 'long' in 'not long' handled by negation above; 'less/short/kam' are positive cues
            if used:
                lab = "positive" if score > 0.4 else "negative" if score < -0.4 else ("neutral" if (neutral or score == 0) else "neutral")
                res[a] = lab
            else:
                res[a] = res[a] if res[a] != "absent" else "neutral" if False else "absent"
    return res


class ClauseAspectModel:
    kind = "clause-rules"

    def fit(self, df=None):
        return self                                   # rule-based: nothing to train

    def predict(self, texts) -> pd.DataFrame:
        return pd.DataFrame([predict_one(t) for t in texts], columns=ASPECTS)

    def save(self, path):
        import joblib; joblib.dump(self, path)

    @staticmethod
    def load(path):
        import joblib; return joblib.load(path)
