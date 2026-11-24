"""
Local inference service for the Spring Boot backend (replaces the placeholder SentimentLexicon).

    python -m medbook_analysis.serve --model tfidf-svm --train-data data/labelled.csv --port 8001
    python -m medbook_analysis.serve --model bert:models/distilbert --port 8001

Endpoints (JSON):
    POST /polarity  {"text": "..."}  ->  {"polarity": -1|0|1, "aspects": {"doctor": "positive", ...}}
    GET  /health
Binds to 127.0.0.1 ONLY, so patient text never leaves the machine (privacy requirement, Section 5.2.1).

Overall polarity of a text = sign(#positive aspects - #negative aspects) over the aspects the model found.
Neutral/absent aspects do not vote; a tie (or no sentiment found) gives 0, matching the lexicon's contract.
"""
from __future__ import annotations
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import numpy as np
from .config import ASPECTS
from .pipeline import get_model
from .synth import load_labelled
from .evaluate import split


def overall_polarity(aspects: dict) -> int:
    pos = sum(v == "positive" for v in aspects.values())
    neg = sum(v == "negative" for v in aspects.values())
    return int(np.sign(pos - neg))


def make_handler(model):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self._send(200, {"status": "ok"}) if self.path == "/health" else self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/polarity":
                return self._send(404, {"error": "not found"})
            try:
                n = int(self.headers.get("Content-Length", "0"))
                text = str(json.loads(self.rfile.read(n) or b"{}").get("text", ""))[:2000]
                asp = {a: v[0] for a, v in model.predict([text]).to_dict("list").items()}
                self._send(200, {"polarity": overall_polarity(asp), "aspects": asp})
            except Exception as e:  # never crash the server on a bad request
                self._send(400, {"error": str(e)})

        def log_message(self, *args):  # do NOT log patient text / requests
            pass
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="tfidf-svm")
    ap.add_argument("--train-data")
    ap.add_argument("--port", type=int, default=8001)
    a = ap.parse_args()
    train = None
    if a.model.startswith("tfidf"):
        if not a.train_data:
            raise SystemExit("--train-data is required for tfidf models")
        train = load_labelled(a.train_data)           # serve trains on ALL labelled data
    model = get_model(a.model, train)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(model))
    print(f"serving {a.model} on http://127.0.0.1:{a.port}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
