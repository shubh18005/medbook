"""
Fine-tuned BERT-type aspect model (synopsis Section 5.2.4 (b)): DistilBERT (default) or BERT.

Architecture: one shared transformer encoder + FIVE classification heads (one per aspect), each
predicting {absent, negative, neutral, positive}. Loss = sum of the five cross-entropies, so the
encoder learns a shared representation of the review and one forward pass gives all aspects
(this is what keeps latency at one model call per review).

Train (needs internet for the pretrained weights, a GPU or Colab is recommended):
    python -m medbook_analysis.bert_model train --data data/labelled.csv --out models/distilbert \
        --model-name distilbert-base-uncased --epochs 4
Smoke test (offline, tiny random model, only proves the code path works):
    python -m medbook_analysis.bert_model smoke
"""
from __future__ import annotations
import argparse
import json
import os
import random
import numpy as np
import pandas as pd
from .config import ASPECTS, LABELS, LABEL2ID, ID2LABEL


def _torch():
    import torch  # imported lazily so the TF-IDF part works without torch installed
    return torch


# ----------------------------------------------------------------------------- model
def build_model(encoder, hidden: int, dropout: float = 0.1):
    torch = _torch()
    nn = torch.nn

    class MultiAspect(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            self.drop = nn.Dropout(dropout)
            self.heads = nn.ModuleList([nn.Linear(hidden, len(LABELS)) for _ in ASPECTS])

        def forward(self, input_ids, attention_mask):
            h = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
            m = attention_mask.unsqueeze(-1).type_as(h)
            pooled = (h * m).sum(1) / m.sum(1).clamp(min=1)       # masked mean pooling
            pooled = self.drop(pooled)
            return torch.stack([head(pooled) for head in self.heads], dim=1)   # (B, 5, 4)

    return MultiAspect()


class BertAspectModel:
    def __init__(self, model, tokenizer, max_len: int = 128, device: str | None = None):
        torch = _torch()
        self.model, self.tok, self.max_len = model, tokenizer, max_len
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    # -------- data
    def _encode(self, texts):
        enc = self.tok(list(texts), padding=True, truncation=True, max_length=self.max_len, return_tensors="pt")
        return enc["input_ids"].to(self.device), enc["attention_mask"].to(self.device)

    @staticmethod
    def _targets(df: pd.DataFrame):
        torch = _torch()
        return torch.tensor([[LABEL2ID[v] for v in row] for row in df[ASPECTS].values], dtype=torch.long)

    # -------- training
    def fit(self, df: pd.DataFrame, epochs: int = 4, batch_size: int = 16, lr: float = 3e-5,
            weight_decay: float = 0.01, warmup_frac: float = 0.1, seed: int = 42, val_df: pd.DataFrame | None = None,
            verbose: bool = True):
        torch = _torch()
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        y = self._targets(df)
        texts = df["text"].tolist()
        n = len(texts)
        steps = epochs * ((n + batch_size - 1) // batch_size)
        opt = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        warm = max(1, int(warmup_frac * steps))
        sched = torch.optim.lr_scheduler.LambdaLR(
            opt, lambda s: (s + 1) / warm if s < warm else max(0.0, (steps - s) / max(1, steps - warm)))
        ce = torch.nn.CrossEntropyLoss()
        history = []
        for ep in range(epochs):
            self.model.train()
            order = np.random.permutation(n)
            tot = 0.0
            for i in range(0, n, batch_size):
                idx = order[i:i + batch_size]
                ids, mask = self._encode([texts[j] for j in idx])
                logits = self.model(ids, mask)                       # (B,5,4)
                loss = sum(ce(logits[:, a, :], y[idx, a].to(self.device)) for a in range(len(ASPECTS)))
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step(); sched.step()
                tot += float(loss) * len(idx)
            rec = {"epoch": ep + 1, "train_loss": tot / n}
            if val_df is not None:
                pred = self.predict(val_df["text"])
                rec["val_acc"] = float(np.mean([(pred[a].values == val_df[a].values).mean() for a in ASPECTS]))
            history.append(rec)
            if verbose:
                print(rec)
        return history

    # -------- inference
    def predict(self, texts, batch_size: int = 64) -> pd.DataFrame:
        torch = _torch()
        texts = list(texts)
        self.model.eval()
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                ids, mask = self._encode(texts[i:i + batch_size])
                out.append(self.model(ids, mask).argmax(-1).cpu().numpy())
        arr = np.concatenate(out) if out else np.zeros((0, len(ASPECTS)), dtype=int)
        return pd.DataFrame({a: [ID2LABEL[int(k)] for k in arr[:, j]] for j, a in enumerate(ASPECTS)})

    # -------- persistence
    def save(self, path: str, model_name: str):
        torch = _torch()
        os.makedirs(path, exist_ok=True)
        torch.save(self.model.state_dict(), os.path.join(path, "weights.pt"))
        self.tok.save_pretrained(path)
        self.model.encoder.config.save_pretrained(path)      # so load() works offline
        json.dump({"model_name": model_name, "max_len": self.max_len, "aspects": ASPECTS, "labels": LABELS},
                  open(os.path.join(path, "meta.json"), "w"))

    @staticmethod
    def load(path: str, device: str | None = None) -> "BertAspectModel":
        torch = _torch()
        from transformers import AutoConfig, AutoModel, AutoTokenizer
        meta = json.load(open(os.path.join(path, "meta.json")))
        tok = AutoTokenizer.from_pretrained(path)
        cfg = AutoConfig.from_pretrained(path) if os.path.exists(os.path.join(path, "config.json")) \
            else AutoConfig.from_pretrained(meta["model_name"])
        enc = AutoModel.from_config(cfg)
        model = build_model(enc, cfg.hidden_size)
        model.load_state_dict(torch.load(os.path.join(path, "weights.pt"), map_location="cpu"))
        return BertAspectModel(model, tok, meta["max_len"], device)


def train_pretrained(df, model_name="distilbert-base-uncased", **kw) -> BertAspectModel:
    """Load the pretrained encoder from the Hugging Face hub and fine-tune it."""
    from transformers import AutoModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name)
    enc = AutoModel.from_pretrained(model_name)
    m = BertAspectModel(build_model(enc, enc.config.hidden_size), tok, kw.pop("max_len", 128))
    m.fit(df, **kw)
    return m


# ----------------------------------------------------------------------------- offline smoke test
class _ToyTokenizer:
    """Whitespace tokenizer with a tiny vocab; ONLY for the offline smoke test."""
    def __init__(self, texts):
        words = sorted({w for t in texts for w in t.lower().split()})
        self.vocab = {"[PAD]": 0, "[UNK]": 1, **{w: i + 2 for i, w in enumerate(words)}}

    def __call__(self, texts, padding=True, truncation=True, max_length=128, return_tensors="pt"):
        torch = _torch()
        seqs = [[self.vocab.get(w, 1) for w in t.lower().split()][:max_length] or [1] for t in texts]
        L = max(len(s) for s in seqs)
        ids = torch.tensor([s + [0] * (L - len(s)) for s in seqs])
        return {"input_ids": ids, "attention_mask": (ids != 0).long()}

    def save_pretrained(self, path):
        json.dump(self.vocab, open(os.path.join(path, "toy_vocab.json"), "w"))


def smoke(n=400, epochs=6):
    """Offline sanity check: tiny random DistilBERT on the synthetic data. Proves that training,
    prediction, saving and the evaluation interface work. Scores here mean NOTHING about DistilBERT."""
    from transformers import DistilBertConfig, DistilBertModel
    from .synth import generate
    from .evaluate import split, aspect_report
    df = generate(n)
    tr, te = split(df)
    tok = _ToyTokenizer(df["text"])
    cfg = DistilBertConfig(vocab_size=len(tok.vocab), dim=64, hidden_dim=128, n_layers=2, n_heads=2, max_position_embeddings=64)
    m = BertAspectModel(build_model(DistilBertModel(cfg), cfg.dim), tok, max_len=48)
    hist = m.fit(tr, epochs=epochs, batch_size=32, lr=2e-3, verbose=False)
    print("loss first->last epoch: %.3f -> %.3f" % (hist[0]["train_loss"], hist[-1]["train_loss"]))
    rep = aspect_report(te, m.predict(te["text"]))
    print(rep.round(3).to_string(index=False))
    return hist


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("--data", required=True); t.add_argument("--out", required=True)
    t.add_argument("--model-name", default="distilbert-base-uncased")
    t.add_argument("--epochs", type=int, default=4); t.add_argument("--batch-size", type=int, default=16)
    t.add_argument("--lr", type=float, default=3e-5); t.add_argument("--seed", type=int, default=42)
    sub.add_parser("smoke")
    a = ap.parse_args()
    if a.cmd == "smoke":
        smoke(); return
    from .synth import load_labelled
    from .evaluate import split, aspect_report, latency_ms
    df = load_labelled(a.data)
    tr, te = split(df, seed=a.seed)
    m = train_pretrained(tr, a.model_name, epochs=a.epochs, batch_size=a.batch_size, lr=a.lr, seed=a.seed, val_df=te)
    print(aspect_report(te, m.predict(te["text"])).round(3).to_string(index=False))
    print("latency ms/review: %.1f" % latency_ms(m.predict, te["text"]))
    m.save(a.out, a.model_name)


if __name__ == "__main__":
    main()
