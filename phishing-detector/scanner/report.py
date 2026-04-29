"""
Batch report generation for phishing scan results.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()


def generate_report(results: list, output_path: str = None) -> dict:
    """
    Summarize batch scan results and optionally save to JSON.

    Each result dict is expected to have keys:
      verdict, confidence, risk_level, traits, details
    """
    total = len(results)
    phishing = [r for r in results if r["verdict"] == "PHISHING"]
    legitimate = [r for r in results if r["verdict"] == "LEGITIMATE"]

    risk_breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        risk_breakdown[r.get("risk_level", "LOW")] += 1

    # Trait frequency
    trait_counts: dict = {}
    for r in results:
        for trait in r.get("traits", {}).get("traits_detected", []):
            trait_counts[trait] = trait_counts.get(trait, 0) + 1

    top_trait = max(trait_counts, key=trait_counts.get) if trait_counts else "none"

    avg_phishing_conf = (
        sum(r["confidence"] for r in phishing) / len(phishing)
        if phishing else 0.0
    )
    avg_legit_conf = (
        sum(r["confidence"] for r in legitimate) / len(legitimate)
        if legitimate else 0.0
    )

    flagged_emails = []
    for r in phishing:
        entry = {k: v for k, v in r.items() if k != "traits"}
        if "text" in r:
            entry["text_preview"] = r["text"][:200]
        flagged_emails.append(entry)

    report = {
        "scan_date": datetime.now(timezone.utc).isoformat(),
        "total_scanned": total,
        "phishing_detected": len(phishing),
        "legitimate": len(legitimate),
        "detection_rate_percent": round(len(phishing) / total * 100, 1) if total else 0.0,
        "avg_phishing_confidence": round(avg_phishing_conf, 2),
        "avg_legitimate_confidence": round(avg_legit_conf, 2),
        "risk_breakdown": risk_breakdown,
        "common_traits": trait_counts,
        "top_trait": top_trait,
        "flagged_emails": flagged_emails,
    }

    # Print summary table
    table = Table(title="Batch Scan Report", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total scanned", str(total))
    table.add_row("Phishing detected", f"[red]{len(phishing)}[/red]")
    table.add_row("Legitimate", f"[green]{len(legitimate)}[/green]")
    table.add_row("Detection rate", f"{report['detection_rate_percent']}%")
    table.add_row("Avg phishing confidence", f"{avg_phishing_conf:.1f}%")
    table.add_row("Avg legit confidence", f"{avg_legit_conf:.1f}%")
    table.add_row("HIGH risk", str(risk_breakdown["HIGH"]))
    table.add_row("MEDIUM risk", str(risk_breakdown["MEDIUM"]))
    table.add_row("LOW risk", str(risk_breakdown["LOW"]))
    table.add_row("Top manipulation trait", top_trait)
    console.print(table)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        console.print(f"\n[green]Report saved to[/green] [cyan]{path}[/cyan]")

    return report
