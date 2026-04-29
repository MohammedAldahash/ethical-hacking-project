"""
Detailed evaluation of the trained phishing detector.
Run from phishing-detector/: python -m train.evaluate
"""

import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

from rich.console import Console
from rich.table import Table

console = Console()


def main():
    console.rule("[bold blue]Phishing Detector — Detailed Evaluation[/bold blue]")

    # ── Check model exists ────────────────────────────────────────────────────
    if not config.MODEL_DIR.exists():
        console.print(
            "[bold red]Error:[/bold red] No trained model found at "
            f"[cyan]{config.MODEL_DIR}[/cyan]\n\n"
            "Train the model first: [bold]python -m train.fine_tune[/bold]"
        )
        sys.exit(1)

    # ── Check dataset ─────────────────────────────────────────────────────────
    if not config.DATASET_PATH.exists():
        console.print(
            "[bold red]Error:[/bold red] No dataset found. "
            "Run [bold]python -m data.generate_dataset_standalone[/bold] first."
        )
        sys.exit(1)

    from transformers import RobertaForSequenceClassification, RobertaTokenizer

    # ── Load data ─────────────────────────────────────────────────────────────
    raw = json.loads(config.DATASET_PATH.read_text())
    texts = [item["text"] for item in raw]
    labels = [item["label"] for item in raw]

    _, test_texts, _, test_labels = train_test_split(
        texts, labels, test_size=config.TEST_SPLIT, random_state=42, stratify=labels
    )

    # ── Load model ────────────────────────────────────────────────────────────
    console.print(f"Loading model from [cyan]{config.MODEL_DIR}[/cyan]")
    tokenizer = RobertaTokenizer.from_pretrained(str(config.MODEL_DIR))
    model = RobertaForSequenceClassification.from_pretrained(str(config.MODEL_DIR))

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    model.to(device)
    model.eval()

    # ── Run predictions ───────────────────────────────────────────────────────
    console.print(f"Running predictions on {len(test_texts)} test samples...")
    all_preds = []
    all_probs = []

    batch_size = 16
    for i in range(0, len(test_texts), batch_size):
        batch = test_texts[i:i + batch_size]
        enc = tokenizer(
            batch,
            max_length=config.MAX_LENGTH,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            outputs = model(**enc)
        probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
        preds = np.argmax(probs, axis=-1)
        all_preds.extend(preds.tolist())
        all_probs.extend(probs.tolist())

    # ── Classification report ─────────────────────────────────────────────────
    report = classification_report(
        test_labels, all_preds,
        target_names=["LEGITIMATE", "PHISHING"],
        output_dict=True,
    )
    console.print("\n[bold]Classification Report:[/bold]")
    cr_table = Table(show_header=True)
    cr_table.add_column("Class", style="bold")
    cr_table.add_column("Precision", justify="right")
    cr_table.add_column("Recall", justify="right")
    cr_table.add_column("F1-Score", justify="right")
    cr_table.add_column("Support", justify="right")
    for cls in ["LEGITIMATE", "PHISHING", "weighted avg"]:
        row = report[cls]
        cr_table.add_row(
            cls,
            f"{row['precision']:.4f}",
            f"{row['recall']:.4f}",
            f"{row['f1-score']:.4f}",
            str(int(row['support'])),
        )
    console.print(cr_table)

    # ── Confusion matrix ──────────────────────────────────────────────────────
    cm = confusion_matrix(test_labels, all_preds)
    console.print("\n[bold]Confusion Matrix:[/bold]")
    cm_table = Table(show_header=True)
    cm_table.add_column("", style="bold")
    cm_table.add_column("Pred: LEGIT", justify="right")
    cm_table.add_column("Pred: PHISHING", justify="right")
    cm_table.add_row("True: LEGIT", str(cm[0][0]), str(cm[0][1]))
    cm_table.add_row("True: PHISHING", str(cm[1][0]), str(cm[1][1]))
    console.print(cm_table)

    # ── Top confident catches ─────────────────────────────────────────────────
    def show_top(title: str, condition, score_fn, color: str):
        entries = [
            (score_fn(all_probs[i]), test_texts[i], test_labels[i], all_preds[i])
            for i in range(len(test_texts)) if condition(i)
        ]
        entries.sort(key=lambda x: x[0], reverse=True)
        console.print(f"\n[bold]{title}[/bold]")
        t = Table(show_header=True)
        t.add_column("Confidence", justify="right", style=color)
        t.add_column("Text (first 80 chars)")
        for score, text, _, _ in entries[:5]:
            snippet = text.replace("\n", " ")[:80] + "..."
            t.add_row(f"{score * 100:.1f}%", snippet)
        console.print(t)

    # Correct phishing detections
    show_top(
        "Top 5 Most Confident Phishing Catches (correct)",
        lambda i: test_labels[i] == 1 and all_preds[i] == 1,
        lambda p: p[1],
        "red",
    )

    # Correct legitimate classifications
    show_top(
        "Top 5 Most Confident Legitimate (correct)",
        lambda i: test_labels[i] == 0 and all_preds[i] == 0,
        lambda p: p[0],
        "green",
    )

    # Misclassified
    console.print("\n[bold]Top 5 Misclassified:[/bold]")
    misclassified = [
        (max(all_probs[i]), test_texts[i], test_labels[i], all_preds[i])
        for i in range(len(test_texts)) if test_labels[i] != all_preds[i]
    ]
    misclassified.sort(key=lambda x: x[0], reverse=True)
    m_table = Table(show_header=True)
    m_table.add_column("True", style="bold")
    m_table.add_column("Pred", style="bold")
    m_table.add_column("Confidence", justify="right")
    m_table.add_column("Text (first 80 chars)")
    for score, text, true_label, pred_label in misclassified[:5]:
        snippet = text.replace("\n", " ")[:80] + "..."
        m_table.add_row(
            config.LABELS[true_label],
            config.LABELS[pred_label],
            f"{score * 100:.1f}%",
            snippet,
        )
    console.print(m_table)

    # ── Save results ──────────────────────────────────────────────────────────
    results = {
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "total_test_samples": len(test_texts),
    }
    results_path = config.MODEL_DIR.parent / "evaluation_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    console.print(f"\n[green]Results saved to[/green] [cyan]{results_path}[/cyan]")


if __name__ == "__main__":
    main()
