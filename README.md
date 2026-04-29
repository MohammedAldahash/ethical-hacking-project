# ICS-442 Email Project

Two complementary email-intelligence tools built for ICS-442:

| Tool | Description |
|---|---|
| **AI Email Campaign CLI** | Write & send personalized sales emails via Groq + Gmail |
| **Phishing Detector** | Detect phishing emails with a fine-tuned RoBERTa model |

---

## Tool 1 — AI Email Campaign CLI
### 100% Free · Powered by Groq + Gmail

A command-line tool that uses AI to write personalized sales emails and send them via Gmail.

### Requirements

| Requirement | Where to get it | Cost |
|---|---|---|
| Node.js v18+ | https://nodejs.org | Free |
| Groq API Key | https://console.groq.com | Free |
| Gmail account | https://gmail.com | Free |
| Gmail App Password | Google Account settings | Free |

### Setup

**Step 1 — Install Node.js**
```bash
node --version   # should show v18 or higher
```

**Step 2 — Get a free Groq API key** at https://console.groq.com → API Keys → Create API Key

**Step 3 — Create a Gmail App Password**
1. Google Account → Security → enable 2-Step Verification
2. Security → App passwords → Mail → Other → Generate
3. Copy the 16-character password

**Step 4 — Clone & install**
```bash
git clone https://github.com/MohammedAldahash/ICS-442-EmailProject.git
cd ICS-442-EmailProject
npm install
```

**Step 5 — Configure**
```bash
node index.js setup
```
Prompts for your Groq key, Gmail address, and App Password. Creates a `.env` file.

### Commands

```bash
node index.js compose          # start a campaign
node index.js compose --dry-run  # preview without sending
node index.js lists            # manage saved contact lists
node index.js setup            # re-run the setup wizard
node index.js --help
```

### Email Tones

| Tone | Best for |
|---|---|
| Cold & Professional | First outreach to executives |
| Urgent & Time-Sensitive | Limited-time offers, deadlines |
| Excited & Enthusiastic | Product launches, big news |
| Warm & Friendly | Relationship-building, warm leads |
| Formal & Corporate | Enterprise, legal, finance sectors |
| Casual & Conversational | Startups, tech, creative industries |

### Project Structure (Tool 1)

```
EmailProject/
├── index.js
├── package.json
├── .env.example
├── .gitignore
├── commands/
│   ├── compose.js
│   └── manage-lists.js
├── lib/
│   ├── llm.js
│   ├── emailSender.js
│   ├── tones.js
│   └── recipients.js
└── data/
    └── recipients.json
```

---

## Tool 2 — Phishing Detector
### Powered by Fine-Tuned RoBERTa · 100% F1 Score

A Python CLI that classifies emails as **PHISHING** or **LEGITIMATE** using a RoBERTa model fine-tuned on a custom dataset of 480 labeled emails.

### Model Performance

| Metric | Score |
|---|---|
| Accuracy | 100% |
| Precision | 100% |
| Recall | 100% |
| F1 | 100% |
| Test samples | 96 (48 per class) |

### Requirements

```bash
pip install -r phishing-detector/requirements.txt
```

Dependencies: `transformers`, `torch`, `datasets`, `scikit-learn`, `accelerate`, `rich`, `typer`

### Train the Model

The trained weights are not included in the repo (11 GB). Train locally:

```bash
cd phishing-detector
python -m train.fine_tune
```

This generates the dataset, fine-tunes RoBERTa, and saves the model to `models/roberta-phishing/`.

> If no local model is found, the scanner automatically falls back to a public HuggingFace model.

### Scan Emails

```bash
cd phishing-detector

# Scan text inline
python -m scanner.cli scan --text "Your account has been suspended. Click here to verify."

# Scan a file
python -m scanner.cli scan --file email.txt

# Scan a folder of .txt / .eml files
python -m scanner.cli scan-batch --folder ./emails/ --output report.json

# Interactive mode (paste and scan in real time)
python -m scanner.cli interactive

# Demo mode (5 built-in example emails)
python -m scanner.cli demo
```

### Run Tests

```bash
cd phishing-detector
python -m pytest tests/ -v
```

11 tests — all pass.

### Project Structure (Tool 2)

```
phishing-detector/
├── __main__.py
├── __init__.py
├── config.py
├── requirements.txt
├── data/
│   ├── generate_dataset.py      # dataset generation
│   ├── dataset.json             # 480 labeled emails
│   └── verify_samples.py
├── train/
│   ├── fine_tune.py             # fine-tunes RoBERTa
│   └── evaluate.py
├── scanner/
│   ├── cli.py                   # Typer CLI (scan / scan-batch / interactive / demo)
│   ├── detect.py                # PhishingDetector class
│   └── report.py                # batch report generator
├── models/
│   ├── evaluation_results.json  # saved eval metrics
│   └── roberta-phishing/        # trained weights (not in repo — train locally)
└── tests/
    └── test_detector.py         # 11 unit tests
```

---

## Privacy & Security

- `.env` contains sensitive keys — never share it or commit it
- `.env`, `node_modules/`, trained model weights, and `__pycache__` are all listed in `.gitignore`
- Groq does not store your prompts permanently
- Emails are sent directly from your Gmail account — use a spare account for SMTP sending
