"""
Build a REAL-email training set from public HuggingFace datasets.

Produces data/dataset.json in the exact format the rest of the pipeline expects:
    [{"text": "<email body>", "label": 0|1}]     # 0 = LEGITIMATE, 1 = PHISHING

Unlike generate_dataset_standalone.py (synthetic templates), this pulls real
phishing + legitimate emails so the detector generalizes beyond its own templates.

Run from phishing-detector/:
    python -m data.build_real_dataset                      # default: 2000 balanced
    python -m data.build_real_dataset --size 2000
    python -m data.build_real_dataset --dataset zefang-liu/phishing-email-dataset
    python -m data.build_real_dataset --mix-synthetic      # also fold in synthetic set

Needs internet access the first time (HuggingFace downloads + caches locally).
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

console = Console()
random.seed(42)

# Candidate real-email datasets on the HuggingFace Hub. The first that loads wins
# (unless one is forced with --dataset). All are public, research-oriented corpora
# built from real emails (Enron / Nazario / SpamAssassin / collected phishing).
CANDIDATE_DATASETS = [
    "zefang-liu/phishing-email-dataset",   # ~18k emails: "Email Text" / "Email Type"
    "ealvaradob/phishing-dataset",         # the corpus behind the fallback model
]

# Column-name candidates we auto-detect (datasets are inconsistent about naming).
TEXT_COLUMNS = ["text", "Email Text", "email", "body", "content", "message", "texts"]
LABEL_COLUMNS = ["label", "Email Type", "type", "class", "target", "labels"]

# Map whatever a dataset calls its labels onto our 0/1 convention.
PHISHING_TOKENS = {"1", "phishing", "phishing email", "spam", "phish", "malicious", "fraud"}
LEGIT_TOKENS = {"0", "legitimate", "safe", "safe email", "ham", "benign", "normal"}

MIN_CHARS = 40        # drop near-empty rows
MAX_CHARS = 8000      # cap very long emails (model truncates to 256 tokens anyway)


def clean_text(raw: str) -> str:
    """Strip HTML, collapse whitespace, drop obvious noise."""
    if not raw:
        return ""
    text = str(raw)
    text = re.sub(r"<[^>]+>", " ", text)            # strip HTML tags
    text = re.sub(r"&[a-z]+;", " ", text)           # strip HTML entities
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)          # collapse blank-line runs
    text = re.sub(r"[ \t]{2,}", " ", text)          # collapse runs of spaces
    return text.strip()


def map_label(value) -> int | None:
    """Return 1 (phishing), 0 (legitimate), or None if unrecognized."""
    if value is None:
        return None
    key = str(value).strip().lower()
    if key in PHISHING_TOKENS:
        return 1
    if key in LEGIT_TOKENS:
        return 0
    # numeric fall-through (e.g. 1.0 / 0.0)
    try:
        num = int(float(key))
        if num in (0, 1):
            return num
    except ValueError:
        pass
    return None


def pick_column(available, candidates, kind):
    for cand in candidates:
        if cand in available:
            return cand
    # case-insensitive retry
    lower = {c.lower(): c for c in available}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    console.print(
        f"[bold red]Could not find a {kind} column.[/bold red] "
        f"Available columns: {list(available)}"
    )
    sys.exit(1)


def load_rows(dataset_name):
    """Load a HF dataset and return a list of (text, label) with labels in {0,1}."""
    from datasets import load_dataset, concatenate_datasets

    console.print(f"Loading [cyan]{dataset_name}[/cyan] from HuggingFace...")
    ds = load_dataset(dataset_name)

    # Merge every split (train/test/validation) into one pool.
    splits = [ds[s] for s in ds.keys()]
    data = concatenate_datasets(splits) if len(splits) > 1 else splits[0]

    cols = data.column_names
    text_col = pick_column(cols, TEXT_COLUMNS, "text")
    label_col = pick_column(cols, LABEL_COLUMNS, "label")
    console.print(f"Using text column [green]'{text_col}'[/green], "
                  f"label column [green]'{label_col}'[/green]")

    rows = []
    for text_raw, label_raw in zip(data[text_col], data[label_col]):
        label = map_label(label_raw)
        if label is None:
            continue
        text = clean_text(text_raw)
        if len(text) < MIN_CHARS:
            continue
        rows.append((text[:MAX_CHARS], label))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Build a real-email phishing dataset.")
    parser.add_argument("--size", type=int, default=2000,
                        help="Total balanced samples to emit (default 2000). "
                             "Use 0 or --all to keep EVERY usable row (unbalanced).")
    parser.add_argument("--all", action="store_true",
                        help="Keep every usable email (no cap, no balancing).")
    parser.add_argument("--dataset", default=None,
                        help="Force a specific HuggingFace dataset id.")
    parser.add_argument("--mix-synthetic", action="store_true",
                        help="Also include the existing synthetic set (dataset_synthetic.json).")
    args = parser.parse_args()

    console.rule("[bold blue]Build REAL phishing dataset[/bold blue]")

    # ── Load from HuggingFace (first candidate that works) ──────────────────────
    sources = [args.dataset] if args.dataset else CANDIDATE_DATASETS
    rows = []
    for name in sources:
        try:
            rows = load_rows(name)
            if rows:
                console.print(f"Loaded [bold]{len(rows)}[/bold] usable rows from {name}")
                break
        except Exception as exc:  # noqa: BLE001 - want to try the next candidate
            console.print(f"[yellow]Could not load {name}: {exc}[/yellow]")
    if not rows:
        console.print("[bold red]No data could be loaded. Check your internet "
                      "connection or pass --dataset explicitly.[/bold red]")
        sys.exit(1)

    # ── Dedupe ──────────────────────────────────────────────────────────────────
    seen = set()
    unique = []
    for text, label in rows:
        key = text[:200]
        if key in seen:
            continue
        seen.add(key)
        unique.append({"text": text, "label": label})

    phishing = [r for r in unique if r["label"] == 1]
    legit = [r for r in unique if r["label"] == 0]
    console.print(f"After cleaning/dedupe: "
                  f"[red]{len(phishing)} phishing[/red], "
                  f"[green]{len(legit)} legitimate[/green]")

    # ── Optionally fold in the synthetic set ────────────────────────────────────
    if args.mix_synthetic:
        synth_path = config.DATA_DIR / "dataset_synthetic.json"
        if synth_path.exists():
            synth = json.loads(synth_path.read_text(encoding="utf-8"))
            for item in synth:
                (phishing if item["label"] == 1 else legit).append(item)
            console.print(f"Mixed in {len(synth)} synthetic samples")
        else:
            console.print("[yellow]--mix-synthetic set but dataset_synthetic.json "
                          "not found; skipping.[/yellow]")

    # ── Select samples ──────────────────────────────────────────────────────────
    random.shuffle(phishing)
    random.shuffle(legit)

    if args.all or args.size == 0:
        # Keep everything — no cap, no balancing. Weighted F1 handles the skew.
        dataset = phishing + legit
        console.print(f"[bold]--all:[/bold] keeping every usable email "
                      f"({len(dataset)} total, unbalanced)")
    else:
        # Balanced sample to the requested size.
        per_class = args.size // 2
        if len(phishing) < per_class or len(legit) < per_class:
            per_class = min(len(phishing), len(legit))
            console.print(f"[yellow]Not enough for {args.size}; using {per_class} "
                          f"per class ({per_class * 2} total).[/yellow]")
        dataset = phishing[:per_class] + legit[:per_class]

    random.shuffle(dataset)

    # ── Write in the pipeline's exact format ────────────────────────────────────
    config.DATASET_PATH.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    table = Table(title="Real Dataset Built", show_header=True)
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total samples", str(len(dataset)))
    table.add_row("Phishing (1)", str(sum(1 for d in dataset if d["label"] == 1)))
    table.add_row("Legitimate (0)", str(sum(1 for d in dataset if d["label"] == 0)))
    table.add_row("Output", str(config.DATASET_PATH))
    console.print(table)
    console.print(
        "\n[green]Done![/green] Next:\n"
        "  [bold]python -m train.fine_tune[/bold]    — train on the real data\n"
        "  [bold]python -m train.evaluate[/bold]     — detailed metrics"
    )


if __name__ == "__main__":
    main()
