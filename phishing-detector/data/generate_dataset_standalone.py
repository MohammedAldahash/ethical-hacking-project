"""
Standalone dataset generator — no Groq API key required.
Generates 200+ phishing and 200+ legitimate email samples using templates.
Run from phishing-detector/: python -m data.generate_dataset_standalone
"""

import json
import random
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

console = Console()
random.seed(42)

# ── Name/company pools ─────────────────────────────────────────────────────────

FIRST_NAMES = ["Ahmed", "Sarah", "Wei", "Priya", "James", "Fatima", "Carlos", "Aisha",
               "Marcus", "Yuki", "Omar", "Elena", "David", "Layla", "Raj", "Sofia"]
LAST_NAMES = ["Al-Rashid", "Chen", "Zhang", "Sharma", "Okafor", "Al-Zahrawi", "Mendoza",
              "Patel", "Thompson", "Tanaka", "Hassan", "Kozlov", "Nkosi", "Al-Farsi", "Iyer"]
TARGET_COMPANIES = ["TechStart Solutions", "DataCorp Analytics", "KFUPM Innovation Lab",
                    "Aramco Digital", "Nexus Labs", "CloudBridge Inc", "SecureNet Systems",
                    "Pinnacle Ventures", "Quantum Dynamics", "BlueWave Technologies"]
TARGET_POSITIONS = ["CTO", "VP of Engineering", "Security Analyst", "IT Director",
                    "Head of Operations", "CIO", "DevOps Lead", "Data Science Manager",
                    "Product Manager", "Engineering Manager"]
SENDER_NAMES = ["Alex Rivera", "Morgan Lee", "Jordan Hayes", "Taylor Brooks",
                "Casey Quinn", "Riley Foster", "Drew Callahan", "Sam Winters"]
SENDER_COMPANIES = ["InnovateTech Corp", "Velocity AI", "StreamFlow Systems", "Apex Solutions",
                    "ClearPath Analytics", "NexGen Software", "BrightEdge Technologies"]
PRODUCTS = ["AI security audit platform", "cloud cost optimizer", "threat intelligence feed",
            "compliance automation suite", "zero-trust network solution", "predictive analytics tool",
            "DevSecOps accelerator", "security awareness training platform"]
DEADLINES = ["this Friday", "end of the month", "next Tuesday", "within 48 hours",
             "before the quarter ends", "this week only", "by midnight tonight"]
DISCOUNTS = ["40%", "50%", "35%", "60%", "a full month free"]
SPOTS = ["3", "5", "2", "7", "10"]
DATES = ["March 14", "April 2", "May 19", "June 7", "July 22", "August 5",
         "September 11", "October 30", "November 15", "December 3"]


def rnd_target():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def rnd_company():
    return random.choice(TARGET_COMPANIES)


def rnd_position():
    return random.choice(TARGET_POSITIONS)


def rnd_sender():
    return random.choice(SENDER_NAMES)


def rnd_sender_co():
    return random.choice(SENDER_COMPANIES)


def rnd_product():
    return random.choice(PRODUCTS)


# ── Phishing templates ─────────────────────────────────────────────────────────

PHISHING_TEMPLATES = {
    "cold_professional": [
        "Subject: Cut {company}'s Security Costs by 40%\n\n{name},\n\nAs {position} at {company}, you're likely aware of the hidden costs in your current security stack. Our {product} has helped teams like yours reduce overhead by 40% while improving threat detection by 3x.\n\nWorth a 15-minute call? Reply and I'll send you a custom analysis.\n\n{sender}\n{sender_co}",
        "Subject: {company}'s Infrastructure Gap — I noticed something\n\n{name},\n\nI analyzed {company}'s public footprint and identified three gaps that are likely costing you significant engineering hours each month. Our {product} closes these automatically.\n\n73 companies in your sector have already made the switch. Can we talk this week?\n\n{sender}",
        "Subject: ROI Analysis for {company}\n\n{name},\n\nBased on {company}'s size and industry, our models estimate you're losing $47K/month to inefficient {product}-related processes. We can cut that in half within 60 days — or you don't pay.\n\nReply to get your free ROI breakdown.\n\n{sender}, {sender_co}",
    ],
    "urgent_fomo": [
        "Subject: Last chance: {discount} off expires {deadline}\n\n{name},\n\nI've been trying to reach you — our {deadline} offer for {company} expires at midnight. You'd be locking in {discount} off our {product} for the next 12 months.\n\nOnly {spots} slots remain at this price. Reply NOW to hold yours.\n\n{sender}",
        "Subject: URGENT: {name}, your competitor just signed up\n\n{name},\n\nOne of {company}'s direct competitors finalized their contract with us yesterday. They'll have our {product} live by {date}.\n\nYou have a narrow window to move before they gain the advantage. Can we talk today?\n\nThis offer closes {deadline}.\n\n{sender}, {sender_co}",
        "Subject: Closing your account offer {deadline}\n\n{name},\n\nThis is the final notice for the exclusive {company} pricing we reserved for you. The board approved a special rate — {discount} off annual plans — but only until {deadline}.\n\nAfter that, it's gone permanently. Reply to lock it in.\n\n{sender}",
    ],
    "excited_launch": [
        "Subject: {name}, you need to see what just launched!\n\n{name},\n\nI'm SO excited to share this — we just released the biggest update to our {product} and I immediately thought of {company}.\n\nThis new version is going to change how your team at {company} handles everything from {position}-level workflows down to daily ops. The results from beta testers have been INSANE — 5x faster, 3x more accurate.\n\nCan I show you a 15-min demo? I promise you'll love it!\n\n{sender}",
        "Subject: Game changer for {company} — just dropped!\n\n{name},\n\nWe've been building this for 18 months and it's finally here. Our new {product} is designed specifically for teams like yours at {company}, and the early results are extraordinary.\n\nI'd love to personally walk you through it. As a {position}, you'll see immediately why this is different from everything else out there.\n\nReply and I'll send your personal demo link today!\n\n{sender}, {sender_co}",
    ],
    "warm_friendly": [
        "Subject: {name}, I've been following {company}'s work\n\n{name},\n\nI hope you don't mind the cold reach-out — I've genuinely been following {company}'s progress in the industry and I'm impressed by what your team has built.\n\nAs someone in a similar space, I think there's real potential for us to help each other. Our {product} has been transformative for teams like yours, and I'd love to share what we've learned.\n\nWould you be open to a casual 15-minute chat? No pitch, just ideas.\n\n{sender}",
        "Subject: Quick question from a fellow {position}\n\n{name},\n\nHoping to connect! I spent three years in a {position} role myself before joining {sender_co}, so I deeply understand the challenges you're navigating at {company}.\n\nOur {product} came out of those exact frustrations. I'd love your honest feedback on it — and if there's a fit, great. If not, I still think you'd find the conversation valuable.\n\nCoffee chat this week?\n\n{sender}",
    ],
    "formal_corporate": [
        "Subject: Formal Proposal: {product} for {company}\n\nDear {name},\n\nI am writing on behalf of {sender_co} to formally present an opportunity that we believe aligns directly with {company}'s strategic objectives.\n\nOur {product} has been adopted by Fortune 500 organizations in your sector to achieve measurable improvements in operational efficiency. I would like to request a formal meeting at your earliest convenience to present our proposal.\n\nPlease find our executive summary attached. I look forward to your response.\n\nYours sincerely,\n{sender}\n{sender_co}",
        "Subject: Strategic Partnership Opportunity — {company}\n\nDear {name},\n\nFollowing our industry research, {sender_co} has identified {company} as an ideal partner for our {product} initiative. Our board has specifically approved a tailored engagement structure for organizations of your caliber.\n\nWe respectfully request 20 minutes of your time to present a confidential proposal that our legal team has prepared exclusively for {company}.\n\nKindly confirm your availability at your earliest convenience.\n\nRespectfully,\n{sender}\nExecutive Vice President, {sender_co}",
    ],
    "casual_conversational": [
        "Subject: hey {name} — random thought about {company}\n\n{name}!\n\nSo I was telling my colleague about some of the challenges companies like {company} deal with and they immediately said 'you should talk to {name}.'\n\nWe built a {product} that's honestly kind of ridiculous how well it works. It's not for everyone but given what you're doing at {company} I think you'd get it immediately.\n\nWanna hop on a call? Totally chill, no pressure whatsoever.\n\n{sender}",
        "Subject: not sure if this is relevant but...\n\n{name},\n\nOkay so this is a bit random but I was chatting with someone who works at {company} (won't say who lol) and they mentioned you're the person to talk to about {product}-type stuff.\n\nWe've been helping a bunch of teams in your space and the results have been kinda wild. Would love to show you what I mean.\n\nHalf-hour call sometime this week? I'll bring the interesting data, you bring the coffee.\n\n{sender}",
    ],
    "credential_phishing": [
        "Subject: Action Required: Verify Your {company} Account\n\nDear {name},\n\nWe detected unusual activity on your {company} corporate account associated with your {position} credentials. To protect your account, please verify your identity within 24 hours.\n\nClick here to verify: [Secure Verification Portal]\n\nIf you do not verify, your account access will be suspended for security reasons.\n\nSecurity Team\n{sender_co} Account Protection",
        "Subject: Password Reset Required — {company} IT Security\n\n{name},\n\nOur systems detected a failed login attempt from an unrecognized device. As a precautionary measure, your {company} account password must be reset immediately.\n\nReset your password here: [Account Security Portal]\n\nThis link expires in 2 hours. If you did not attempt to log in, contact IT immediately.\n\nIT Security\n{sender_co}",
        "Subject: Your {company} Microsoft 365 license expires tonight\n\n{name},\n\nYour Microsoft 365 license for {company} is set to expire at 11:59 PM tonight. To avoid disruption to your {position} workflows, please renew immediately.\n\nRenew now: [License Renewal Portal]\n\nFailure to act will result in loss of access to all Office applications and email.\n\nMicrosoft Licensing Team",
    ],
    "invoice_payment": [
        "Subject: Invoice #INV-{invoice} Overdue — Immediate Action Required\n\n{name},\n\nThis is a final notice regarding Invoice #INV-{invoice} for ${amount} which is now {days} days overdue from {company}.\n\nTo avoid late fees and service suspension, please process payment immediately:\n\nPayment Portal: [Secure Payment Link]\nAmount Due: ${amount}\nDue Date: {date} (OVERDUE)\n\nContact us immediately if you believe this is an error.\n\n{sender}\nAccounts Receivable, {sender_co}",
        "Subject: Urgent: Wire Transfer Authorization Needed — {company}\n\n{name},\n\nI need your immediate assistance with a time-sensitive wire transfer for an acquisition deal involving {company}. This is strictly confidential and must be processed today before close of business.\n\nPlease reply with your authorization code or call me directly at the number below. The board is waiting.\n\nThis is urgent — please do not delay.\n\n{sender}\nCFO, {sender_co}",
    ],
    "spear_phishing": [
        "Subject: RE: {company} Q4 security review — follow up\n\n{name},\n\nFollowing up on our brief exchange at the conference last month. As {position} at {company}, you mentioned the challenges with your current security posture.\n\nOur {product} was built specifically for organizations at {company}'s stage. I've prepared a custom analysis based on {company}'s public-facing infrastructure — I think you'll find it eye-opening.\n\nCan we reconnect this week? I'll send the report as soon as we confirm a time.\n\n{sender}, {sender_co}",
        "Subject: {name} — your team's LinkedIn activity flagged something\n\n{name},\n\nI was reviewing hiring patterns for {position} roles and noticed {company} has been growing the engineering team significantly. That usually signals specific scaling challenges.\n\nI work with several companies at your exact inflection point. Our {product} has prevented three of them from hitting the infrastructure wall you're likely approaching.\n\nWould you be open to a 20-minute technical deep-dive? I'll come prepared with {company}-specific insights.\n\n{sender}",
    ],
}


def gen_phishing() -> str:
    category = random.choice(list(PHISHING_TEMPLATES.keys()))
    template = random.choice(PHISHING_TEMPLATES[category])
    return template.format(
        name=rnd_target(),
        company=rnd_company(),
        position=rnd_position(),
        sender=rnd_sender(),
        sender_co=rnd_sender_co(),
        product=rnd_product(),
        deadline=random.choice(DEADLINES),
        discount=random.choice(DISCOUNTS),
        spots=random.choice(SPOTS),
        date=random.choice(DATES),
        invoice=str(random.randint(10000, 99999)),
        amount=str(random.randint(500, 50000)),
        days=str(random.randint(7, 45)),
    )


# ── Hard / ambiguous phishing templates (label=1) ─────────────────────────────
# BEC and impersonation attacks styled as internal emails.
# Uses colleague names and internal project vocabulary so the model
# cannot distinguish these from standard legitimate emails on surface patterns alone.

HARD_PHISHING_TEMPLATES = [
    # BEC: CFO impersonation requesting wire transfer
    "Hi {name},\n\nI'm in back-to-back meetings and can't take calls right now. I need you to process a wire transfer of ${amount} to close the {project} deal before close of business — this is time-sensitive. I'll sign off on the paperwork when I'm back tomorrow.\n\nThanks,\n{colleague}",
    # HR impersonation: collecting bank details under guise of payroll audit
    "Hi {name},\n\nWe're updating our payroll records before the next pay cycle and need to verify the bank account we have on file for you. Please reply confirming your current account details are unchanged, or provide the new information if anything has changed.\n\nHR Operations",
    # IT impersonation: credentials needed for system migration
    "Hi {name},\n\nAs part of the {project} infrastructure migration, we need to verify that your directory credentials are correctly mapped to the new environment. Could you reply with your employee ID and confirm your registered email address?\n\nIT Infrastructure Team",
    # Executive impersonation: gift card request
    "Hey {name},\n\nQuick favor — I'm in a long meeting and need you to pick up ${amount} in Amazon gift cards for a client hospitality gift. I'll reimburse you by end of day. Send me the redemption codes when you have them — this is urgent.\n\n{colleague}",
    # Vendor impersonation: redirecting a legitimate payment to a new account
    "Hi {name},\n\nOur company recently updated our banking details. Please ensure the outstanding invoice for ${amount} on the {project} account is redirected to our new account — I'll send the wire details in a follow-up email shortly. Please acknowledge receipt.\n\n{colleague}\nFinance Operations",
    # New employee social engineering: mapping the org chart
    "Hi {name},\n\nI just joined the team this week and I'm still finding my way around. Someone told me you're the right person to talk to about the {project} infrastructure. Could you help me understand who I should loop in for questions on the backend architecture?\n\nThanks so much,\n{colleague}",
    # Fake internal security team: requesting password confirmation
    "Hi {name},\n\nThis is the internal security team. We're following up on a SIEM alert associated with your account credentials. As a precaution, could you confirm your password hasn't been shared externally recently? Just a quick reply is fine.\n\nSecurity Operations",
    # Colleague impersonation: requesting document via personal email
    "Hey {name},\n\nI'm working from home today and having trouble with VPN. Can you send the {project} proposal to my personal email? I need to review it before the client call at 3 PM. Thanks for covering for me.\n\n{colleague}",
    # BEC: urgent payment redirection
    "Hi {name},\n\nPlease note that the vendor for the {project} engagement has changed their banking details. The invoice currently pending for ${amount} should be redirected to their new account. Please hold off on the existing payment until I send the updated wire details.\n\n{colleague}",
    # Fake internal survey collecting employee data
    "Hi {name},\n\nWe're running a quick internal survey as part of the {project} post-mortem process. Could you share your employee ID, current role, and a brief note on your involvement? This is internal only and will be kept confidential.\n\nThank you,\n{colleague}",
    # Impersonating an external consultant who claims leadership approval
    "Hi {name},\n\nI'm an external consultant working with your leadership team on the {project} initiative. {colleague} suggested I reach out to you directly for some background context on the current architecture. Would you be available for a 15-minute call this week?\n\nBest,\n{sender}",
    # Fake internal security alert: "is this you?" — harvesting confirmation
    "Hi {name},\n\nJust checking — did you log into the {project} admin portal from a new device recently? We flagged an access event that doesn't match your usual location. If this was you, just reply to confirm and we'll clear the alert.\n\nIT Security, {colleague}",
    # Fake helpdesk: needs credentials to replicate an issue
    "Hi {name},\n\nWe have a ticket open for an issue affecting your account in the {project} environment. To resolve it quickly, could you share your login credentials temporarily so we can replicate the problem? They'll only be used for this session and then cleared.\n\nHelp Desk",
    # BEC: request to approve a contract before a fake deadline
    "Hi {name},\n\nThe legal team has finalized the {project} vendor agreement. Given the {date} deadline, I need a quick go-ahead from your side before we counter-sign. Can you reply with your approval? I'll handle the signature once I have your confirmation.\n\n{colleague}",
    # Fake recruiter gathering competitive intelligence about the team
    "Hi {name},\n\nI'm a recruiter specializing in {position} roles and was referred to you by {colleague}. I'm not trying to poach you — I'm doing market research. Would you be open to sharing some context on what your team is working on technically? Just a 10-minute call.\n\n{sender}",
    # IT impersonation: MFA reset requiring identity confirmation
    "Hi {name},\n\nWe're cycling MFA tokens for all accounts in the {project} infrastructure group. To verify your identity before issuing the new token, please reply with your employee ID and confirm your registered phone number is still correct.\n\nIT Security Operations",
    # Pretending to be a known vendor contact following up on project access
    "Hi {name},\n\nGreat working with you on the {project} deployment last month. Following up on the integration environment access — we still haven't received the credentials on our side and it's blocking our configuration work. Please send when you get a chance.\n\n{sender}, {sender_co}",
    # Fake platform admin: account expiry requiring reply to stay active
    "Hi {name},\n\nYour access to the {project} shared workspace expires at the end of this week unless renewed. To keep your permissions active, please reply with your team name and confirm you're still working on the project.\n\n{colleague}\nPlatform Administration",
    # Internal-looking financial verification collecting payment details
    "Hi {name},\n\nWe're reconciling the approved vendor payment list and need to verify the account details we have on file for the {project} vendor. Could you confirm the banking details you used for the last payment? We want to make sure our records match.\n\n{colleague}\nFinance Operations",
    # Fake SOC 2 audit collecting system access inventory
    "Hi {name},\n\nAs part of our annual SOC 2 audit, we're collecting an inventory of active credentials and system access from key personnel. Please reply with the list of platforms and systems you currently access in your {position} role. Internal audit purposes only.\n\nCompliance Team",
]


# ── Hard / ambiguous legitimate templates (label=0) ───────────────────────────
# Real commercial and vendor emails that use urgency, scarcity, and company-name
# targeting — vocabulary patterns the model associates with phishing — but are
# genuinely legitimate service notifications, renewals, or vendor outreach.

HARD_LEGITIMATE_TEMPLATES = [
    # Real SaaS usage limit warning — urgency but from your own vendor
    "Dear {name},\n\nYour {company} account on {sender_co} is approaching its monthly {product} limit — you've used 87% of your allocation. To avoid service interruption after {date}, please upgrade your plan now. Current pricing is only guaranteed until the end of this billing cycle.\n\n{sender}\n{sender_co} Account Management",
    # Real security login alert — looks like phishing but is a genuine notification
    "Dear {name},\n\nA sign-in to your {sender_co} account was detected from a new device on {date}. If this was you, no action is needed. If you don't recognize this activity, please secure your account immediately by resetting your password at {sender_co}.com/security.\n\nSecurity Team, {sender_co}",
    # Real vendor pricing expiration — uses "competitors" and urgency
    "Hi {name},\n\nWe've been working with {company} on the {product} contract renewal and wanted to flag that our current pricing expires on {date}. After that, rates increase by 25%. I'm only authorized to honor this rate for the next 5 business days — please let me know how you'd like to proceed.\n\n{sender}, {sender_co}",
    # Real benefits enrollment — aggressive deadline, legitimate HR
    "Dear {name},\n\nOPEN ENROLLMENT CLOSES {date}. This is your last chance to update your health, dental, and vision coverage for the coming year. Employees who miss this window keep last year's selections with no exceptions. Log in to the HR portal and confirm your choices now.\n\nHuman Resources, {sender_co}",
    # Real conference with hard seat limit
    "Hi {name},\n\nOnly {spots} seats remain at our {date} {product} summit. We have CISOs and engineering leads from companies like {company} already registered. Once we hit venue capacity there are no waitlists. Register now to secure your seat.\n\n{sender}\n{sender_co} Events",
    # Real cold outreach from legitimate vendor — ROI claims, sounds like phishing
    "Hi {name},\n\nI'll be direct: companies like {company} are spending 3x more than necessary on {product}. We've helped teams in your exact situation cut that cost significantly. I have a specific proposal for {company} — can we connect for 15 minutes? No demos, just numbers.\n\n{sender}, {sender_co}",
    # Real password expiry notice — lockout warning, legitimate IT communication
    "Dear {name},\n\nYour {sender_co} account password expires in 3 days on {date}. After that you will be locked out until a manual identity verification is completed, which can take up to 24 hours. Update your password now through the standard employee portal to avoid disruption.\n\nIT Security, {sender_co}",
    # Real subscription renewal — "competitors upgraded" framing, legitimate sales
    "Hi {name},\n\nYour {sender_co} subscription renews on {date}. We've released major updates to {product} this quarter — features that several companies in your sector have already adopted. I'd love to walk you through what's new before your renewal. Demo slots are limited this week.\n\n{sender}",
    # Real overdue invoice with late fee — looks like phishing invoice scam
    "Dear {name},\n\nInvoice #{invoice} for ${amount} from {sender_co} is now 15 days past due. A late fee of 1.5% per month will be applied if payment is not received by {date}. Please process via our payment portal or reply with a remittance confirmation.\n\n{sender}\nAccounts Receivable, {sender_co}",
    # Real IT access audit — credential re-authentication language but legitimate
    "Dear {name},\n\nAs part of our annual access review, all {position} accounts at {company} will be audited starting {date}. You may be asked to re-authenticate to certain systems as we verify entitlements. This is a standard compliance process — no action required today.\n\n{sender}\nIT Governance, {sender_co}",
    # Real "competitor just signed" framing — legitimate sales transparency
    "Hi {name},\n\nI wanted to let you know that three companies in your sector — including one direct competitor of {company} — have deployed {sender_co}'s {product} in the last 60 days. I'm sharing this for transparency, not pressure. Happy to share what they're doing if useful.\n\n{sender}",
    # Real expiring free trial with discount offer
    "Hi {name},\n\nYour free trial of {sender_co}'s {product} expires on {date}. We've seen strong engagement from your {company} team. To keep your setup and data, upgrade before the trial ends — I can authorize a 30% discount if you commit this week.\n\n{sender}",
    # Real contract expiry with data deletion warning
    "Dear {name},\n\nFinal reminder: your service agreement with {sender_co} expires on {date}. After expiration, your {company} team will lose access to {product} and associated data may be deleted within 30 days under our data retention policy. Please renew now to avoid data loss.\n\n{sender}\nAccount Management, {sender_co}",
    # Real compliance training mandate with access revocation threat
    "Dear {name},\n\nAll employees in {position} roles must complete the mandatory data privacy training by {date}. Employees who miss this deadline will have system access revoked until training is completed. The training takes approximately 45 minutes. Log in now to complete it.\n\nCompliance & Risk, {sender_co}",
    # Real unusual API usage alert from a real platform
    "Dear {name},\n\nWe detected an unusual spike in API calls from your {company} integration on {date}, triggering an automated rate-limit alert. Your access has been temporarily throttled. To restore full access, review your integration settings and contact {sender} directly.\n\n{sender_co} Platform Support",
    # Real cold outreach with loss aversion framing — sounds very phishy
    "Hi {name},\n\nI noticed {company} hasn't upgraded from the legacy {product} version. Several clients in your exact situation waited too long and faced serious issues at renewal. I'd like to personally make sure that doesn't happen to you. Can we talk this week?\n\n{sender}, {sender_co}",
    # Real authorized special pricing from an account manager
    "Hi {name},\n\nI've been authorized to extend a pricing offer to {company} that isn't publicly available: ${amount} for a 12-month enterprise {product} license — 40% below our standard rate. This offer expires on {date} and is exclusive to existing contacts. Let me know if you want to move forward.\n\n{sender}, {sender_co}",
    # Real exclusive roundtable with scarcity and social proof
    "Hi {name},\n\nYou're invited to a closed roundtable on {date} for {position} leaders in the {product} space. Only {spots} seats are available. Participants from {company} peers and industry leaders will be there. This is off the record — no pitches, just peer discussion.\n\n{sender}, {sender_co}",
    # Real account inactivity notice with data deletion deadline
    "Dear {name},\n\nThis is a notice from {sender_co} that accounts inactive for 12+ months are subject to deletion under our data retention policy. Our records show your {company} account has not been accessed since before {date}. To retain your data, log in before {date}.\n\n{sender_co} Data Operations",
    # Real accounts receivable follow-up before collections
    "Dear {name},\n\nWe're writing regarding Invoice #{invoice} for ${amount} from {sender_co}, outstanding since {date} with no payment or dispute on file. To avoid this being forwarded to collections, please confirm receipt and provide a timeline for resolution.\n\n{sender}\nAccounts Receivable, {sender_co}",
]


def gen_hard_phishing() -> str:
    # Use internal-style names so these look like standard legitimate emails
    template = random.choice(HARD_PHISHING_TEMPLATES)
    return template.format(
        name=random.choice(LEG_NAMES),
        company=rnd_company(),
        position=rnd_position(),
        sender=rnd_sender(),
        sender_co=rnd_sender_co(),
        product=rnd_product(),
        project=random.choice(LEG_PROJECTS),
        colleague=random.choice(LEG_COLLEAGUES),
        date=random.choice(LEG_DATES),
        spots=random.choice(SPOTS),
        invoice=str(random.randint(10000, 99999)),
        amount=str(random.randint(500, 50000)),
    )


def gen_hard_legitimate() -> str:
    # Use external-style names so these look like standard phishing emails
    template = random.choice(HARD_LEGITIMATE_TEMPLATES)
    return template.format(
        name=rnd_target(),
        company=rnd_company(),
        position=rnd_position(),
        sender=rnd_sender(),
        sender_co=rnd_sender_co(),
        product=rnd_product(),
        colleague=random.choice(["Marcus", "Sofia", "Raj", "Yuki", "Elena", "Carlos"]),
        project=random.choice(LEG_PROJECTS),
        date=random.choice(DATES),
        spots=random.choice(SPOTS),
        invoice=str(random.randint(10000, 99999)),
        amount=str(random.randint(500, 50000)),
    )


# ── Legitimate templates ───────────────────────────────────────────────────────

LEGITIMATE_TEMPLATES = [
    # Internal team
    "Hi {name},\n\nJust a quick update on the {project} project. We completed the sprint review yesterday and everything is on track for the {date} deadline. The QA team flagged two minor issues that {colleague} is addressing today.\n\nLet me know if you have any questions.\n\n{sign}",
    "Hey {name},\n\nMeeting notes from this morning's standup are attached. Main action items: you're on deck for the API documentation by EOD Friday, and {colleague} will handle the deployment pipeline review.\n\n{sign}",
    "Hi {name},\n\nFYI — the CI/CD pipeline will be down for maintenance tonight from 11 PM to 1 AM. Please make sure to push any critical changes before then.\n\nThanks,\n{sign}",
    "Hey {name},\n\nI've pushed the hotfix to staging. Can you do a quick sanity check before we promote to prod? Mostly want eyes on the auth flow.\n\nThanks,\n{colleague}",
    "Hi {name},\n\nReminder that the architecture review for the {project} migration is tomorrow at 2 PM in the Zoom room. Please bring your current diagram and any blockers you want discussed.\n\nSee you then,\n{sign}",
    # IT notifications
    "Dear {name},\n\nThis is a reminder from IT that your network password expires in 7 days. Please update it at your earliest convenience via the employee portal at intranet.company.com/password.\n\nIT Help Desk",
    "Hello {name},\n\nWe'll be performing scheduled maintenance on the file servers this Saturday, {date}, from 8 AM to 12 PM. During this window, access to shared drives will be unavailable. Please plan accordingly.\n\nIT Operations",
    "Hi {name},\n\nYour VPN certificate has been renewed and will take effect on {date}. No action is needed on your end — the client will update automatically on your next login.\n\nIT Security",
    # HR
    "Dear {name},\n\nOpen enrollment for the 2025 benefits year begins on {date}. You have until November 30th to make your selections in the HR portal.\n\nHuman Resources",
    "Hi {name},\n\nJust a reminder that the office will be closed on {date} for the national holiday.\n\nHR Team",
    "Hello {name},\n\nYour request for 3 days of PTO ({date} to {date2}) has been approved. Enjoy your time off!\n\nBest,\n{sign}",
    "Dear {name},\n\nYour annual performance review is scheduled for {date} at 10 AM. Please complete the self-assessment form in Workday at least 48 hours in advance.\n\nPeople Operations",
    # Colleagues
    "Hey {name}, are you free for lunch on {date}? A few of us are heading to the new place near the office. Let me know!\n\n— {colleague}",
    "Hi {name},\n\nSharing the Q3 budget spreadsheet with you as discussed. I've granted you edit access. Let me know if anything looks off in the forecasting tab.\n\nCheers,\n{colleague}",
    "Hey {name}, quick question — do you know who owns the legacy auth module? I need to ask about the session timeout behavior.\n\nThanks,\n{colleague}",
    "Hi {name},\n\nI noticed the staging environment is throwing 502 errors again. I've restarted the backend service and it seems stable now. Keeping an eye on it.\n\n{colleague}",
    "Hey {name}, did you get a chance to review the PR I sent yesterday? No rush, just want to make sure it's not blocking you.\n\n{colleague}",
    # Customer support
    "Dear {name},\n\nYour support ticket #48291 has been resolved. The issue with the CSV export was caused by a timezone bug. The fix has been deployed to production.\n\nSupport Team",
    "Hello {name},\n\nYour order has shipped! Expected delivery is {date}. You can track it using the tracking number in your original order confirmation email.\n\nCustomer Success",
    # Newsletter/digest
    "Hi {name},\n\nHere's your weekly engineering digest for the week of {date}:\n\n• 3 new RFCs posted for review\n• Incident postmortem for last Tuesday's outage is ready\n• New onboarding guide published in Confluence\n\nHave a great weekend!\n{sign}",
    "Good morning {name},\n\nThe latest blog post on our security hardening guide is now live. We've covered certificate rotation, secrets management, and our new IAM approach.\n\n{sign}",
    # Calendar
    "Hi {name},\n\nI'd like to reschedule our 1:1 from Tuesday to Wednesday at 3 PM if that works for you. Let me know and I'll update the invite.\n\nThanks,\n{colleague}",
    "Hello {name},\n\nThis is a meeting invitation for the Q4 planning session on {date} at 10 AM in Conference Room B. Agenda is attached.\n\nSee you there,\n{colleague}",
    # Additional variety
    "Hi {name},\n\nJust confirming receipt of the {project} documentation you sent over. I'll review it by EOD {date} and send feedback.\n\n{sign}",
    "Hey {name},\n\nThe new employee onboarding checklist has been updated in Confluence. Please take a look and let {colleague} know if anything is missing before the new hire starts on {date}.\n\n{sign}",
]

LEG_NAMES = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Irene", "Jack",
             "Karen", "Leo", "Mia", "Nathan", "Olivia", "Pete"]
LEG_COLLEAGUES = ["Marcus", "Sofia", "Raj", "Yuki", "Omar", "Elena", "Carlos", "Priya", "Alex", "Sam"]
LEG_PROJECTS = ["Phoenix", "Atlas", "Horizon", "Nova", "Vertex", "Stratum", "Beacon", "Nexus", "Orion", "Pulse"]
LEG_SIGNS = ["Best,\nAlex", "Thanks,\nMorgan", "Cheers,\nJordan", "Regards,\nTaylor",
             "— Casey", "Best regards,\nRiley", "Thanks,\nDrew"]
LEG_DATES = ["March 14", "April 2", "May 19", "June 7", "July 22",
             "August 5", "September 11", "October 30", "November 15", "December 3"]


def gen_legitimate() -> str:
    template = random.choice(LEGITIMATE_TEMPLATES)
    return template.format(
        name=random.choice(LEG_NAMES),
        colleague=random.choice(LEG_COLLEAGUES),
        project=random.choice(LEG_PROJECTS),
        sign=random.choice(LEG_SIGNS),
        date=random.choice(LEG_DATES),
        date2=random.choice(LEG_DATES),
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    console.rule("[bold blue]Standalone Dataset Generator (No API Key Required)[/bold blue]")

    PHISHING_COUNT = 240
    LEGITIMATE_COUNT = 240
    HARD_PHISHING_COUNT = 60
    HARD_LEGITIMATE_COUNT = 60

    samples: list[dict] = []
    category_counts: dict[str, int] = {k: 0 for k in PHISHING_TEMPLATES}

    console.print(f"Generating [bold]{PHISHING_COUNT}[/bold] standard phishing samples...")
    for _ in range(PHISHING_COUNT):
        category = random.choice(list(PHISHING_TEMPLATES.keys()))
        template = random.choice(PHISHING_TEMPLATES[category])
        text = template.format(
            name=rnd_target(),
            company=rnd_company(),
            position=rnd_position(),
            sender=rnd_sender(),
            sender_co=rnd_sender_co(),
            product=rnd_product(),
            deadline=random.choice(DEADLINES),
            discount=random.choice(DISCOUNTS),
            spots=random.choice(SPOTS),
            date=random.choice(DATES),
            invoice=str(random.randint(10000, 99999)),
            amount=str(random.randint(500, 50000)),
            days=str(random.randint(7, 45)),
        )
        samples.append({"text": text, "label": 1})
        category_counts[category] += 1

    console.print(f"Generating [bold]{HARD_PHISHING_COUNT}[/bold] hard/ambiguous phishing samples...")
    for _ in range(HARD_PHISHING_COUNT):
        samples.append({"text": gen_hard_phishing(), "label": 1})

    console.print(f"Generating [bold]{LEGITIMATE_COUNT}[/bold] standard legitimate samples...")
    for _ in range(LEGITIMATE_COUNT):
        samples.append({"text": gen_legitimate(), "label": 0})

    console.print(f"Generating [bold]{HARD_LEGITIMATE_COUNT}[/bold] hard/ambiguous legitimate samples...")
    for _ in range(HARD_LEGITIMATE_COUNT):
        samples.append({"text": gen_hard_legitimate(), "label": 0})

    random.shuffle(samples)

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.DATASET_PATH.write_text(json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")

    phishing_count = sum(1 for s in samples if s["label"] == 1)
    legit_count = sum(1 for s in samples if s["label"] == 0)

    table = Table(title="Dataset Summary", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("Total samples", str(len(samples)))
    table.add_row("Phishing (standard)", str(PHISHING_COUNT))
    table.add_row("Phishing (hard/ambiguous)", str(HARD_PHISHING_COUNT))
    table.add_row("Legitimate (standard)", str(LEGITIMATE_COUNT))
    table.add_row("Legitimate (hard/ambiguous)", str(HARD_LEGITIMATE_COUNT))
    table.add_row("Total phishing", str(phishing_count))
    table.add_row("Total legitimate", str(legit_count))
    for cat, count in category_counts.items():
        table.add_row(f"  Category: {cat}", str(count))
    table.add_row("Saved to", str(config.DATASET_PATH))

    console.print(table)
    console.print("\n[green]Dataset saved![/green] Next step: [bold]python -m train.fine_tune[/bold]")


if __name__ == "__main__":
    main()
