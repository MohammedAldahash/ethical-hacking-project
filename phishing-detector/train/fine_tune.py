"""
Fine-tune RoBERTa on the generated phishing dataset.
Run from phishing-detector/: python -m train.fine_tune
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

from rich.console import Console
from rich.table import Table

console = Console()


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "precision": precision_score(labels, preds, average="weighted", zero_division=0),
        "recall": recall_score(labels, preds, average="weighted", zero_division=0),
        "f1": f1_score(labels, preds, average="weighted", zero_division=0),
    }


def main():
    torch.manual_seed(42)
    np.random.seed(42)

    console.rule("[bold blue]RoBERTa Phishing Detector — Fine-Tuning[/bold blue]")

    # ── Load dataset ───────────────────────────────────────────────────────────
    if not config.DATASET_PATH.exists():
        console.print(
            "[bold red]Error:[/bold red] No dataset found at "
            f"[cyan]{config.DATASET_PATH}[/cyan]\n\n"
            "Generate it first:\n"
            "  [bold]python -m data.generate_dataset_standalone[/bold]  (no API key needed)\n"
            "  [bold]python -m data.generate_dataset[/bold]              (uses Groq LLM)"
        )
        sys.exit(1)

    raw = json.loads(config.DATASET_PATH.read_text())
    texts = [item["text"] for item in raw]
    labels = [item["label"] for item in raw]
    console.print(f"Loaded [bold]{len(texts)}[/bold] samples "
                  f"([green]{labels.count(0)} legitimate[/green], "
                  f"[red]{labels.count(1)} phishing[/red])")

    # ── Train/test split ───────────────────────────────────────────────────────
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels,
        test_size=config.TEST_SPLIT,
        random_state=42,
        stratify=labels,
    )
    console.print(f"Split: {len(train_texts)} train / {len(test_texts)} test")

    # ── Lazy imports (heavy deps) ──────────────────────────────────────────────
    from datasets import Dataset
    from transformers import (
        RobertaForSequenceClassification,
        RobertaTokenizer,
        Trainer,
        TrainingArguments,
        EarlyStoppingCallback,
    )

    # ── Device ────────────────────────────────────────────────────────────────
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    console.print(f"Device: [bold]{device}[/bold]")

    # ── Tokenizer ─────────────────────────────────────────────────────────────
    console.print(f"Loading tokenizer: [cyan]{config.BASE_MODEL}[/cyan]")
    tokenizer = RobertaTokenizer.from_pretrained(config.BASE_MODEL)

    def tokenize(texts_batch, labels_batch):
        enc = tokenizer(
            texts_batch,
            max_length=config.MAX_LENGTH,
            truncation=True,
            padding="max_length",
        )
        enc["labels"] = labels_batch
        return enc

    train_enc = tokenize(train_texts, train_labels)
    test_enc = tokenize(test_texts, test_labels)

    train_dataset = Dataset.from_dict(train_enc)
    test_dataset = Dataset.from_dict(test_enc)
    train_dataset.set_format("torch")
    test_dataset.set_format("torch")

    # ── Model ─────────────────────────────────────────────────────────────────
    console.print(f"Loading model: [cyan]{config.BASE_MODEL}[/cyan]")
    model = RobertaForSequenceClassification.from_pretrained(
        config.BASE_MODEL,
        num_labels=config.NUM_LABELS,
    )

    # ── Training arguments ────────────────────────────────────────────────────
    checkpoints_dir = str(config.MODEL_DIR / "checkpoints")
    training_args = TrainingArguments(
        output_dir=checkpoints_dir,
        num_train_epochs=config.EPOCHS,
        per_device_train_batch_size=config.BATCH_SIZE,
        per_device_eval_batch_size=config.BATCH_SIZE,
        learning_rate=config.LEARNING_RATE,
        warmup_ratio=config.WARMUP_RATIO,
        weight_decay=config.WEIGHT_DECAY,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir="./logs",
        report_to="none",
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    console.print("\n[bold]Starting training...[/bold]")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start

    # ── Save ──────────────────────────────────────────────────────────────────
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(config.MODEL_DIR))
    tokenizer.save_pretrained(str(config.MODEL_DIR))
    console.print(f"Model saved to [cyan]{config.MODEL_DIR}[/cyan]")

    # ── Final eval ────────────────────────────────────────────────────────────
    metrics = trainer.evaluate()

    table = Table(title="Final Evaluation Metrics", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Accuracy", f"{metrics.get('eval_accuracy', 0):.4f}")
    table.add_row("Precision", f"{metrics.get('eval_precision', 0):.4f}")
    table.add_row("Recall", f"{metrics.get('eval_recall', 0):.4f}")
    table.add_row("F1 (weighted)", f"{metrics.get('eval_f1', 0):.4f}")
    table.add_row("Training time", f"{elapsed:.1f}s")

    console.print(table)
    console.print(
        "\n[green]Training complete![/green] Next steps:\n"
        "  [bold]python -m train.evaluate[/bold]   — detailed evaluation\n"
        "  [bold]python -m scanner.cli demo[/bold]  — run the scanner"
    )


if __name__ == "__main__":
    main()
