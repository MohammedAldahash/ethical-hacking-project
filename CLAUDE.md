# CLAUDE.md

Guidance for working in this repository.

## What this repo is

Two related pieces for an **ICS-442 ethical-hacking / security course project**:

1. **AI Email Campaign tool** (repo root) — a Node.js CLI that uses an LLM (Groq
   `llama-3.3-70b`) to generate personalized emails across 6 tones and send them.
   This is the *offensive* / red-team half. Educational, authorized-testing context.
2. **`phishing-detector/`** — a Python RoBERTa classifier that detects phishing
   emails. This is the *defensive* / blue-team counterpart and is where most ML
   work happens.

> **Note:** `EmailProject/` **is** the ICS-442 project directory itself — there is
> no separate "ICS-442 Project" subfolder. The detector lives in
> `phishing-detector/` under it.

## Layout

```
EmailProject/
├── index.js, commands/, lib/, data/   # Node email-campaign tool (offensive half)
│   ├── lib/llm.js                      # Groq LLM email generation
│   └── .env                            # GROQ_API_KEY lives here
└── phishing-detector/                  # Python detector (defensive half)
    ├── config.py                       # ALL paths + hyperparameters (edit here)
    ├── data/
    │   ├── dataset.json                # training data: [{"text": str, "label": 0|1}]
    │   ├── generate_dataset.py         # build dataset via Groq LLM (needs ../.env)
    │   └── generate_dataset_standalone.py  # build dataset from templates (no API key)
    ├── train/
    │   ├── fine_tune.py                # fine-tune roberta-base -> models/roberta-phishing/
    │   └── evaluate.py                 # detailed eval + confusion matrix
    ├── scanner/
    │   ├── detect.py                   # PhishingDetector class (ML + regex traits)
    │   ├── cli.py                      # Typer CLI: scan / scan-batch / interactive / demo
    │   └── report.py
    ├── tests/test_detector.py          # pytest suite
    └── models/roberta-phishing/        # saved model (gitignored, created by training)
```

## Data contract (important)

Everything downstream depends on one format. `dataset.json` is a JSON array of:

```json
{"text": "<full email body as plain text>", "label": 0}
```

- `label`: **0 = LEGITIMATE, 1 = PHISHING** (see `config.LABELS`).
- Any new data source (real emails, new generators) **must** emit this exact shape
  so `train/fine_tune.py` and `train/evaluate.py` work unchanged.

## Common commands (run from `phishing-detector/`)

```bash
pip install -r requirements.txt
python -m data.generate_dataset_standalone   # regenerate template dataset
python -m train.fine_tune                     # train -> models/roberta-phishing/
python -m train.evaluate                      # detailed metrics
python -m scanner.cli demo                     # 5 built-in examples
python -m scanner.cli scan --text "..."        # scan one email
python -m scanner.cli scan-batch --folder ./emails/
python -m pytest tests/ -v                     # run tests
```

## Key config knobs (`phishing-detector/config.py`)

`BASE_MODEL`, `MAX_LENGTH` (256), `EPOCHS` (4), `BATCH_SIZE` (8),
`LEARNING_RATE` (2e-5), `TEST_SPLIT` (0.2), `DEFAULT_THRESHOLD` (0.70).
If no local model exists, `detect.py` falls back to the HuggingFace public model
`ealvaradob/bert-finetuned-phishing`.

## Conventions / gotchas

- **Windows encoding:** always pass `encoding="utf-8"` to `write_text()` / `open()`
  (default cp1256 breaks on non-ASCII email content).
- Terminal output uses ASCII markers (`[OK]`/`[!]`), not Unicode glyphs — Windows
  consoles choke on them.
- `transformers` v5: use `top_k=None`, not the removed `return_all_scores=True`.
- Scripts run as modules (`python -m ...`) from inside `phishing-detector/`; each
  inserts the parent dir on `sys.path` to import `config`.

## Current state (as of 2026-10-06)

- `dataset.json`: **600 samples** (300 phishing / 300 legitimate), all synthetic
  (templates + LLM). The model scores ~100% F1 on this — a sign it has learned the
  *templates*, not real phishing. Generalization to real-world email is unverified.
- **Direction:** move to a larger (~2k) dataset built from **real** public phishing
  and legitimate corpora so the detector generalizes beyond its own templates.

## Scope

This is authorized coursework in a controlled setting. Work on the **detector**
(defensive side) freely. Treat real email data as sensitive: use public,
research-licensed corpora, keep raw dumps out of git, never commit anyone's
personal mailbox content.
