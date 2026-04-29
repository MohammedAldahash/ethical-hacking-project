"""
CLI for the phishing detector.
Run from phishing-detector/:
  python -m scanner.cli scan --text "..."
  python -m scanner.cli scan --file email.txt
  python -m scanner.cli scan-batch --folder ./emails/
  python -m scanner.cli interactive
  python -m scanner.cli demo
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

app = typer.Typer(help="Phishing email detector powered by fine-tuned RoBERTa.")
console = Console()

# ── Demo emails ────────────────────────────────────────────────────────────────

DEMO_EMAILS = [
    {
        "label": "PHISHING",
        "text": (
            "Subject: Last chance — 50% off expires TONIGHT\n\n"
            "Ahmed,\n\n"
            "I've been trying to reach you all week. Our AI security audit platform "
            "offer for DataCorp expires at midnight tonight — that's 50% off the annual plan. "
            "Only 3 slots remain at this price and your competitor TechStart just signed up yesterday.\n\n"
            "This is a limited time offer. Act now or lose it permanently.\n\n"
            "Alex Rivera\nVelocity AI"
        ),
    },
    {
        "label": "PHISHING",
        "text": (
            "Subject: Action Required: Verify Your DataCorp Account\n\n"
            "Dear Sarah,\n\n"
            "We detected unusual login activity on your DataCorp corporate account. "
            "To protect your credentials, please verify your identity within 24 hours "
            "by clicking the secure verification link below.\n\n"
            "Failure to verify will result in immediate account suspension.\n\n"
            "IT Security Team\nDataCorp Account Protection"
        ),
    },
    {
        "label": "PHISHING",
        "text": (
            "Subject: Wire Transfer Authorization Needed — CONFIDENTIAL\n\n"
            "James,\n\n"
            "I need your immediate assistance with a confidential wire transfer for an "
            "acquisition deal. This must be processed today before close of business. "
            "Do not share this with anyone else on the team.\n\n"
            "Please reply with your authorization code immediately. The board is waiting.\n\n"
            "Morgan Lee\nCFO, Apex Solutions"
        ),
    },
    {
        "label": "LEGITIMATE",
        "text": (
            "Hi Alice,\n\n"
            "Just a quick update on the Phoenix project. We completed the sprint review "
            "yesterday and everything is on track for the March 14 deadline. The QA team "
            "flagged two minor issues that Marcus is addressing today.\n\n"
            "Let me know if you have any questions.\n\nBest,\nAlex"
        ),
    },
    {
        "label": "LEGITIMATE",
        "text": (
            "Dear Bob,\n\n"
            "This is a reminder from IT that your network password expires in 7 days. "
            "Please update it at your earliest convenience via the employee portal at "
            "intranet.company.com/password.\n\nIT Help Desk"
        ),
    },
]


# ── Result rendering ───────────────────────────────────────────────────────────

def render_result(result: dict, email_preview: str = ""):
    verdict = result["verdict"]
    confidence = result["confidence"]
    risk = result["risk_level"]
    traits = result["traits"]

    is_phishing = verdict == "PHISHING"
    border_style = "bold red" if is_phishing else "bold green"
    icon = "[!]" if is_phishing else "[OK]"

    lines = []
    lines.append(f"  {icon}   [bold]{verdict}[/bold]              Risk: [bold]{risk}[/bold]")
    lines.append(f"  Confidence: {confidence:.1f}%")

    if is_phishing and traits["traits_detected"]:
        lines.append("")
        lines.append("  Manipulation traits found:")
        for flag in traits["flags"]:
            lines.append(f"  • {flag}")
        lines.append(f"  Manipulation score: {traits['manipulation_score']:.2f}")
        lines.append("")
        lines.append("  [bold]Action:[/bold] Do NOT click any links or reply.")
        lines.append("  Verify sender via a second channel (phone, Slack).")
    elif is_phishing:
        lines.append("  No specific manipulation traits detected by keyword scan.")
        lines.append("")
        lines.append("  [bold]Action:[/bold] Treat with caution. Verify the sender.")
    else:
        if traits["traits_detected"]:
            lines.append(f"  Note: {traits['trait_count']} soft trait(s) detected — low risk.")
        else:
            lines.append("  No manipulation traits detected.")

    if email_preview:
        lines.append("")
        preview = email_preview.replace("\n", " ")[:100]
        lines.append(f"  [dim]Preview: {preview}...[/dim]")

    console.print(Panel(
        "\n".join(lines),
        border_style=border_style,
        padding=(0, 1),
    ))


def load_detector(threshold: float = None):
    from scanner.detect import PhishingDetector
    try:
        det = PhishingDetector(threshold=threshold)
        source = det._model_source
        if source == "huggingface":
            console.print(
                "[yellow]Note: Using public fallback model (no local model trained yet). "
                "Run [bold]python -m train.fine_tune[/bold] for best results.[/yellow]\n"
            )
        return det
    except Exception as exc:
        console.print(f"[bold red]Failed to load model:[/bold red] {exc}")
        raise typer.Exit(1)


# ── Commands ───────────────────────────────────────────────────────────────────

@app.command()
def scan(
    text: str = typer.Option(None, "--text", "-t", help="Email text to scan"),
    file: Path = typer.Option(None, "--file", "-f", help="Path to .txt or .eml file"),
    threshold: float = typer.Option(None, "--threshold", help="Override detection threshold (0-1)"),
):
    """Scan a single email for phishing."""
    if text is None and file is None:
        console.print("[red]Provide --text or --file.[/red]")
        raise typer.Exit(1)

    if file:
        if not file.exists():
            console.print(f"[red]File not found:[/red] {file}")
            raise typer.Exit(1)
        text = file.read_text(encoding="utf-8", errors="replace")

    detector = load_detector(threshold)
    result = detector.scan(text)
    render_result(result, text)


@app.command(name="scan-batch")
def scan_batch(
    folder: Path = typer.Argument(..., help="Folder containing .txt or .eml files"),
    threshold: float = typer.Option(None, "--threshold", help="Override detection threshold (0-1)"),
    output: Path = typer.Option(None, "--output", "-o", help="Save JSON report to this path"),
):
    """Scan all .txt and .eml files in a folder."""
    if not folder.exists() or not folder.is_dir():
        console.print(f"[red]Folder not found:[/red] {folder}")
        raise typer.Exit(1)

    files = list(folder.glob("*.txt")) + list(folder.glob("*.eml"))
    if not files:
        console.print("[yellow]No .txt or .eml files found.[/yellow]")
        raise typer.Exit(0)

    detector = load_detector(threshold)

    all_results = []
    for f in files:
        email_text = f.read_text(encoding="utf-8", errors="replace")
        result = detector.scan(email_text)
        console.print(f"\n[bold]{f.name}[/bold]")
        render_result(result, email_text)
        all_results.append({"file": str(f.name), **result})

    # Summary table
    console.print("\n")
    from scanner.report import generate_report
    generate_report(all_results, str(output) if output else None)


@app.command()
def interactive(
    threshold: float = typer.Option(None, "--threshold", help="Override detection threshold (0-1)"),
):
    """Interactive mode — paste emails and get results in real time."""
    detector = load_detector(threshold)

    console.print(Panel(
        "[bold blue]Phishing Detector — Interactive Mode[/bold blue]\n\n"
        "Paste email content, then press Enter twice to scan.\n"
        "Type [bold]quit[/bold] and press Enter to exit.",
        border_style="blue",
    ))

    while True:
        console.print("\n[bold cyan]Email content:[/bold cyan] (Enter twice to scan, 'quit' to exit)")
        lines = []
        try:
            while True:
                line = input()
                if line.strip().lower() == "quit":
                    console.print("[green]Goodbye![/green]")
                    return
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            console.print("\n[green]Goodbye![/green]")
            return

        text = "\n".join(lines).strip()
        if text:
            result = detector.scan(text)
            render_result(result, text)
        else:
            console.print("[yellow]Empty input — skipped.[/yellow]")


@app.command()
def demo(
    threshold: float = typer.Option(None, "--threshold", help="Override detection threshold (0-1)"),
):
    """Run a demo scan on 5 built-in example emails (3 phishing, 2 legitimate)."""
    detector = load_detector(threshold)

    console.print(Panel(
        "[bold blue]Phishing Detector Demo[/bold blue]\n"
        "Scanning 5 built-in example emails (3 phishing, 2 legitimate)...",
        border_style="blue",
    ))

    correct = 0
    for i, demo_email in enumerate(DEMO_EMAILS, 1):
        expected = demo_email["label"]
        console.print(f"\n[bold]Email {i}/5[/bold] (expected: {expected})")
        result = detector.scan(demo_email["text"])
        render_result(result, demo_email["text"])
        if result["verdict"] == expected:
            correct += 1
            console.print(f"  [green]CORRECT[/green]")
        else:
            console.print(f"  [red]INCORRECT[/red] (expected {expected})")

    console.print(f"\n[bold]Demo complete: {correct}/5 correct[/bold]")

    table = Table(title="Demo Summary")
    table.add_column("#", justify="right")
    table.add_column("Expected")
    table.add_column("Got")
    table.add_column("Match")
    for i, demo_email in enumerate(DEMO_EMAILS, 1):
        result = detector.scan(demo_email["text"])
        match = "OK" if result["verdict"] == demo_email["label"] else "X"
        color = "green" if match == "OK" else "red"
        table.add_row(
            str(i),
            demo_email["label"],
            result["verdict"],
            f"[{color}]{match}[/{color}]",
        )
    console.print(table)


if __name__ == "__main__":
    app()
