"""
Generate phishing training dataset by calling the ICS-442 tool's LLM (Groq Llama-3.3-70b).
Also generates legitimate email samples entirely in Python.
Run from phishing-detector/: python -m data.generate_dataset
"""

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

console = Console()

ICS442_DIR = config.ICS442_DIR
ENV_FILE = ICS442_DIR / ".env"
HELPER_SCRIPT = Path(__file__).parent / "_generate_helper.mjs"

# ── Diversity pools ────────────────────────────────────────────────────────────

TARGET_NAMES = [
    "Ahmed Al-Rashid", "Sarah Chen", "Wei Zhang", "Priya Sharma", "James Okafor",
    "Fatima Al-Zahrawi", "Carlos Mendoza", "Aisha Patel", "Marcus Thompson",
    "Yuki Tanaka", "Omar Hassan", "Elena Kozlov", "David Nkosi", "Layla Al-Farsi",
    "Raj Iyer", "Sofia Andersen",
]

TARGET_COMPANIES = [
    "TechStart Solutions", "DataCorp Analytics", "KFUPM Innovation Lab",
    "Aramco Digital", "Nexus Labs", "CloudBridge Inc", "SecureNet Systems",
    "Pinnacle Ventures", "Quantum Dynamics", "BlueWave Technologies",
]

TARGET_POSITIONS = [
    "CTO", "VP of Engineering", "Security Analyst", "IT Director",
    "Head of Operations", "Chief Information Officer", "DevOps Lead",
    "Data Science Manager", "Product Manager", "Engineering Manager",
]

SENDER_NAMES = [
    "Alex Rivera", "Morgan Lee", "Jordan Hayes", "Taylor Brooks",
    "Casey Quinn", "Riley Foster", "Drew Callahan", "Sam Winters",
    "Pat Morrison", "Avery Nguyen",
]

SENDER_COMPANIES = [
    "InnovateTech Corp", "Velocity AI", "StreamFlow Systems", "Apex Solutions",
    "ClearPath Analytics", "NexGen Software", "BrightEdge Technologies",
    "CoreSync Platform", "DataSphere Inc", "TrustShield Security",
]

PRODUCTS = [
    "AI-powered security audit platform", "cloud infrastructure optimizer",
    "real-time threat intelligence feed", "automated compliance management suite",
    "zero-trust network access solution", "predictive analytics dashboard",
    "DevSecOps pipeline accelerator", "employee security awareness training platform",
    "API gateway with built-in fraud detection", "ML-based email filtering system",
]

INDUSTRIES = [
    "FinTech", "Healthcare IT", "Oil & Gas", "E-commerce", "SaaS",
    "Government IT", "Education Technology", "Manufacturing", "Telecom",
]

PAIN_POINTS = [
    "struggling with legacy security systems and compliance gaps",
    "facing increasing cloud costs with unpredictable scaling",
    "dealing with a recent data breach and reputational damage",
    "overwhelmed by manual security audit processes",
    "experiencing high employee turnover in engineering teams",
    "trying to accelerate digital transformation on a tight budget",
    "managing multi-cloud environments with poor visibility",
    "failing SOC 2 audits due to incomplete controls",
]

CTAS = [
    "Schedule a 15-minute demo this week",
    "Book a free security assessment",
    "Reply to claim your 30-day free trial",
    "Join our exclusive webinar on Thursday",
    "Accept a complimentary risk report for your company",
    "Reply and I'll send you a custom ROI analysis",
    "Let's set up a quick 10-minute call",
    "Click the link to access your personalized demo",
]

VALUE_PROPS = [
    "reduces audit time by 60%, eliminates false positives, integrates in under 2 hours",
    "cuts cloud spend by 35%, provides real-time anomaly detection, no vendor lock-in",
    "blocks 99.8% of phishing attempts, deploys in minutes, GDPR compliant out of the box",
    "automates 80% of compliance tasks, generates audit-ready reports, SOC2 certified",
    "zero-trust architecture, microsegmentation, works with your existing stack",
]

TONES = ["cold", "urgent", "excited", "warm", "formal", "casual"]

# ── Legitimate email templates ─────────────────────────────────────────────────

LEGITIMATE_TEMPLATES = [
    # Internal team updates
    "Hi {name},\n\nJust a quick update on the {project} project. We completed the sprint review yesterday and everything is on track for the {date} deadline. The QA team flagged two minor issues that {colleague} is addressing today.\n\nLet me know if you have any questions.\n\n{sign}",
    "Hey {name},\n\nMeeting notes from this morning's standup are attached. Main action items: you're on deck for the API documentation by EOD Friday, and {colleague} will handle the deployment pipeline review.\n\n{sign}",
    "Hi {name},\n\nFYI — the CI/CD pipeline will be down for maintenance tonight from 11 PM to 1 AM. Please make sure to push any critical changes before then.\n\nThanks,\n{sign}",
    # IT notifications
    "Dear {name},\n\nThis is a reminder from IT that your network password expires in 7 days. Please update it at your earliest convenience via the employee portal at intranet.company.com/password.\n\nIT Help Desk",
    "Hello {name},\n\nWe'll be performing scheduled maintenance on the file servers this Saturday, {date}, from 8 AM to 12 PM. During this window, access to shared drives will be unavailable. Please plan accordingly.\n\nIT Operations",
    "Hi {name},\n\nYour two-factor authentication backup codes were regenerated as requested. Please find them in the attached secure PDF (password sent separately via SMS).\n\nIT Security Team",
    # HR communications
    "Dear {name},\n\nOpen enrollment for the 2025 benefits year begins on {date}. You have until November 30th to make your selections. Please log in to the HR portal to review your options.\n\nHuman Resources",
    "Hi {name},\n\nJust a reminder that the office will be closed on {date} for the national holiday. If you need to reach someone urgently, please use the emergency contact list on the intranet.\n\nHR Team",
    "Hello {name},\n\nYour request for 3 days of PTO ({date} to {date2}) has been approved. Enjoy your time off!\n\nBest,\n{sign}",
    # Colleague messages
    "Hey {name}, are you free for lunch on Thursday? A few of us are heading to the new Thai place near the office. Let me know!\n\n— {colleague}",
    "Hi {name},\n\nSharing the Q3 budget spreadsheet with you as discussed. I've granted you edit access. Let me know if anything looks off in the forecasting tab.\n\nCheers,\n{colleague}",
    "Hey {name}, quick question — do you know who owns the legacy auth module? I need to ask about the session timeout behavior and can't find it in the docs.\n\nThanks,\n{colleague}",
    # Customer support
    "Dear {name},\n\nYour support ticket #48291 has been resolved. The issue with the CSV export feature was caused by a timezone bug in our reporting engine. The fix has been deployed to production.\n\nThanks for your patience.\nSupport Team",
    "Hello {name},\n\nYour order #ORD-9921 has shipped! Expected delivery is {date}. You can track it at: [tracking link in the original message]\n\nThanks for shopping with us.",
    # Newsletter/digest
    "Hi {name},\n\nHere's your weekly engineering digest for the week of {date}:\n\n• 3 new RFCs posted for review\n• Incident postmortem for last Tuesday's outage is ready\n• New onboarding guide published in Confluence\n\nHave a great weekend!\n{sign}",
    "Good morning {name},\n\nThe latest blog post on our security hardening guide is now live. We've covered certificate rotation, secrets management with Vault, and our new approach to least-privilege IAM roles.\n\nFeel free to share it with your team.\n\n{sign}",
    # Calendar
    "Hi {name},\n\nI'd like to reschedule our 1:1 from Tuesday to Wednesday at 3 PM if that works for you. Please let me know and I'll update the calendar invite.\n\nThanks,\n{colleague}",
    "Hello {name},\n\nThis is a meeting invitation for the Q4 planning session on {date} at 10 AM in Conference Room B (and Zoom for remote attendees). Agenda is attached.\n\nSee you there,\n{colleague}",
    # Simple colleague check-ins
    "Hi {name}, just checking in — did you get a chance to review the PR I sent yesterday? No rush, just want to make sure it's not blocking you.\n\n{colleague}",
    "Hey {name},\n\nI noticed the staging environment is throwing 502 errors again. I've restarted the backend service and it seems to be fine now. Keeping an eye on it.\n\n{colleague}",
]

LEG_NAMES = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Irene", "Jack"]
LEG_COLLEAGUES = ["Marcus", "Sofia", "Raj", "Yuki", "Omar", "Elena", "Carlos", "Priya"]
LEG_PROJECTS = ["Phoenix", "Atlas", "Horizon", "Nova", "Vertex", "Stratum", "Beacon", "Nexus"]
LEG_SIGNS = ["Best,\nAlex", "Thanks,\nMorgan", "Cheers,\nJordan", "Regards,\nTaylor", "— Casey"]
LEG_DATES = [
    "March 14", "April 2", "May 19", "June 7", "July 22",
    "August 5", "September 11", "October 30", "November 15", "December 3",
]


def gen_legitimate_email() -> str:
    template = random.choice(LEGITIMATE_TEMPLATES)
    return template.format(
        name=random.choice(LEG_NAMES),
        colleague=random.choice(LEG_COLLEAGUES),
        project=random.choice(LEG_PROJECTS),
        sign=random.choice(LEG_SIGNS),
        date=random.choice(LEG_DATES),
        date2=random.choice(LEG_DATES),
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_env_key() -> str | None:
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("GROQ_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key and key != "your_groq_api_key_here":
                return key
    return None


def check_node_modules():
    nm = ICS442_DIR / "node_modules"
    if not nm.exists():
        console.print("[yellow]Installing npm dependencies in ICS-442 project...[/yellow]")
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(ICS442_DIR),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]npm install failed:[/red] {result.stderr}")
            sys.exit(1)


def call_helper(args_dict: dict, env: dict) -> dict | None:
    try:
        result = subprocess.run(
            ["node", str(HELPER_SCRIPT), json.dumps(args_dict)],
            cwd=str(config.PROJECT_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            try:
                err = json.loads(stderr)
                console.print(f"[red]LLM error:[/red] {err.get('error', stderr)}")
            except Exception:
                console.print(f"[red]Node error:[/red] {stderr}")
            return None
        return json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        console.print("[red]Request timed out[/red]")
        return None
    except Exception as exc:
        console.print(f"[red]Unexpected error:[/red] {exc}")
        return None


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    random.seed(42)

    console.rule("[bold blue]Phishing Dataset Generator (ICS-442 LLM Mode)[/bold blue]")

    # Validate GROQ_API_KEY
    groq_key = load_env_key()
    if not groq_key:
        console.print(
            "[bold red]Error:[/bold red] GROQ_API_KEY not found in "
            f"[cyan]{ENV_FILE}[/cyan]\n\n"
            "  Option A: Run [bold]node index.js[/bold] in the EmailProject folder "
            "and complete setup.\n"
            "  Option B: Use the standalone generator (no API key needed):\n"
            "            [bold]python -m data.generate_dataset_standalone[/bold]"
        )
        sys.exit(1)

    # Check node_modules
    check_node_modules()

    # Build subprocess env
    proc_env = os.environ.copy()
    proc_env["GROQ_API_KEY"] = groq_key

    PHISHING_PER_TONE = 20
    total_phishing = len(TONES) * PHISHING_PER_TONE  # 120
    total_legitimate = 120

    samples: list[dict] = []
    tone_counts: dict[str, int] = {t: 0 for t in TONES}

    # ── Generate phishing samples ──────────────────────────────────────────────
    console.print(f"\n[bold]Generating {total_phishing} phishing emails via Groq LLM...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Phishing emails", total=total_phishing)

        generated = 0
        for tone in TONES:
            for i in range(PHISHING_PER_TONE):
                target_name = random.choice(TARGET_NAMES)
                args = {
                    "targetName": target_name,
                    "targetCompany": random.choice(TARGET_COMPANIES),
                    "targetPosition": random.choice(TARGET_POSITIONS),
                    "industry": random.choice(INDUSTRIES),
                    "painPoint": random.choice(PAIN_POINTS),
                    "senderName": random.choice(SENDER_NAMES),
                    "senderCompany": random.choice(SENDER_COMPANIES),
                    "product": random.choice(PRODUCTS),
                    "valueProps": random.choice(VALUE_PROPS),
                    "cta": random.choice(CTAS),
                    "tone": tone,
                }

                progress.update(
                    task,
                    description=f"[{generated + 1}/{total_phishing}] tone={tone}, target={target_name.split()[0]}",
                )

                result = call_helper(args, proc_env)

                # Retry once on failure
                if result is None:
                    time.sleep(5)
                    result = call_helper(args, proc_env)

                if result and "subject" in result and "body" in result:
                    text = result["subject"] + "\n\n" + result["body"]
                    samples.append({"text": text, "label": 1})
                    tone_counts[tone] += 1

                generated += 1
                progress.advance(task)

                if generated < total_phishing:
                    time.sleep(2)

    # ── Generate legitimate samples ────────────────────────────────────────────
    console.print(f"\n[bold]Generating {total_legitimate} legitimate email samples...[/bold]")
    for _ in range(total_legitimate):
        samples.append({"text": gen_legitimate_email(), "label": 0})

    # ── Save dataset ───────────────────────────────────────────────────────────
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.DATASET_PATH.write_text(json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Summary ────────────────────────────────────────────────────────────────
    phishing_count = sum(1 for s in samples if s["label"] == 1)
    legit_count = sum(1 for s in samples if s["label"] == 0)

    table = Table(title="Dataset Summary", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("Total samples", str(len(samples)))
    table.add_row("Phishing", str(phishing_count))
    table.add_row("Legitimate", str(legit_count))
    for tone, count in tone_counts.items():
        table.add_row(f"  Tone: {tone}", str(count))
    table.add_row("Saved to", str(config.DATASET_PATH))

    console.print(table)
    console.print("\n[green]Dataset saved![/green] Next step: [bold]python -m train.fine_tune[/bold]")


if __name__ == "__main__":
    main()
