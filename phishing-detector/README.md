# Phishing Email Detector

A RoBERTa-based phishing email detector, built as the defensive counterpart to the AI Email Campaign tool in the parent folder. It detects LLM-generated phishing emails by fine-tuning on the exact style of emails the attacker tool produces.

---

## How It Works

The ICS-442 Email Campaign tool (sibling folder) uses Groq's Llama-3.3-70b to generate highly personalized phishing emails across 6 tones: cold, urgent, excited, warm, formal, and casual. This detector is trained on those exact emails — so it learns the precise patterns, persuasion tactics, and language that LLM-powered phishing tools produce.

**Architecture:**

```
Email Text
    │
    ▼
RobertaTokenizer (max 256 tokens)
    │
    ▼
RoBERTa Base (125M params)
    │
    ▼
Classification Head (2 classes)
    │
    ├─► PHISHING (confidence %)
    └─► LEGITIMATE (confidence %)
         +
    Trait Analyzer (regex patterns)
         │
         └─► Urgency / Social Proof / Scarcity / Authority /
             Reciprocity / Personalization / Emotional Pressure /
             Impersonation Signals
```

---

## Quick Start

```bash
cd phishing-detector
pip install -r requirements.txt

# Option A: Generate dataset using the ICS-442 tool's LLM (needs Groq API key in ../.env)
python -m data.generate_dataset

# Option B: Generate dataset without an API key (uses hardcoded templates — works immediately)
python -m data.generate_dataset_standalone

# Train the model (~5–30 min depending on hardware)
python -m train.fine_tune

# Evaluate accuracy on the test set
python -m train.evaluate

# Run the scanner
python -m scanner.cli demo                          # 5 built-in examples
python -m scanner.cli scan --text "Hi Ahmed, limited time offer..."
python -m scanner.cli scan --file path/to/email.txt
python -m scanner.cli scan-batch --folder ./emails/
python -m scanner.cli interactive

# Run tests
python -m pytest tests/ -v
```

---

## Dataset Generation

### Option A — LLM-generated (best accuracy)

Calls the ICS-442 tool's `generateEmail()` function via a Node.js subprocess to produce 120 phishing emails using Groq's Llama-3.3-70b (same model as the attacker tool), across all 6 tones. Requires `GROQ_API_KEY` in `../.env`.

### Option B — Standalone (no API key)

Generates 240 phishing + 240 legitimate samples using hardcoded templates across 9 phishing categories:
1. Cold/professional unsolicited sales pitches  
2. Urgent/FOMO with fake deadlines  
3. Excited product launch announcements  
4. Warm/friendly fake rapport building  
5. Formal corporate impersonation  
6. Casual social engineering  
7. Credential phishing (account verification, password reset)  
8. Invoice/payment phishing  
9. Spear phishing (targeted, references role/company)  

---

## Accuracy

Accuracy depends on dataset quality:

| Dataset | Expected F1 |
|---------|-------------|
| Standalone templates | ~0.92–0.96 |
| LLM-generated (Groq) | ~0.88–0.94 |
| Mixed (both) | ~0.90–0.95 |

Template-based datasets tend to score higher because the patterns are more distinct. LLM-generated data is harder to classify (more realistic) but produces a model that generalizes better against real phishing.

---

## Manipulation Trait Detection

Beyond the ML classification, the detector uses regex pattern matching to flag psychological manipulation tactics:

| Trait | Example Triggers |
|-------|-----------------|
| urgency | "limited time", "act now", "expires", "deadline" |
| social_proof | "teams like yours", "industry leaders", "trusted by" |
| authority | "CEO", "mandatory", "required by", "IT Security" |
| scarcity | "only 3 spots", "limited availability", "last chance" |
| reciprocity | "free", "complimentary", "no obligation", "gift" |
| personalization | "tailored for", "based on your", "I noticed you" |
| emotional_pressure | "you're missing out", "falling behind", "competitors have" |
| impersonation_signals | "confidential", "wire transfer", "verify your account" |

---

## Project Structure

```
phishing-detector/
├── config.py                          # Central configuration
├── requirements.txt
├── __main__.py                        # Entry point (python -m phishing_detector)
├── data/
│   ├── generate_dataset.py            # Generates samples via Groq LLM
│   ├── generate_dataset_standalone.py # Generates samples without API key
│   ├── _generate_helper.mjs           # Node.js bridge to ICS-442 LLM
│   └── dataset.json                   # Generated training data
├── train/
│   ├── fine_tune.py                   # Fine-tunes roberta-base
│   └── evaluate.py                    # Detailed evaluation + error analysis
├── scanner/
│   ├── detect.py                      # PhishingDetector class
│   ├── cli.py                         # Typer CLI (scan, interactive, demo)
│   └── report.py                      # Batch report generation
├── tests/
│   └── test_detector.py               # Pytest test suite (10 tests)
└── models/
    └── roberta-phishing/              # Saved model (after training)
```

---

## Limitations

- **512 token limit**: Emails longer than ~380 words are truncated. The first 256 tokens are used.
- **Text only**: No email header or sender metadata analysis. A spoofed sender won't be caught unless the email body has phishing signals.
- **Template bias**: Training on templates means the model may miss novel phishing styles. Retrain periodically.
- **False positives on legitimate sales**: Aggressive but genuine sales emails may trigger "urgent" or "personalization" traits and edge over the threshold.
- **Retraining required**: As phishing tactics evolve, the model needs new training data to stay current.

---

## Fallback Model

If no local model has been trained yet, the tool automatically falls back to [`ealvaradob/bert-finetuned-phishing`](https://huggingface.co/ealvaradob/bert-finetuned-phishing) from HuggingFace. This makes the `demo` command work immediately without any training. Train the local model for optimal results against LLM-generated phishing.
