"""One-shot script to replace HARD_PHISHING_TEMPLATES and HARD_LEGITIMATE_TEMPLATES
with completely new designs that create genuine label noise for the model."""
import re
from pathlib import Path

SRC = Path("data/generate_dataset_standalone.py")
text = SRC.read_text(encoding="utf-8")

# ── New HARD_PHISHING_TEMPLATES ────────────────────────────────────────────────
# Zero phishing vocabulary — structurally identical to standard LEGITIMATE templates.
# The model should classify these as LEGITIMATE (creating genuine misclassifications).
NEW_HP = '''# ── Hard / ambiguous phishing templates (label=1) ─────────────────────────────
# Impersonation / pretexting attacks using ZERO phishing vocabulary.
# Structurally identical to the standard legitimate templates: same internal
# colleague names, project names, IT/HR/team tone, no urgency, no product
# pitches, no financial asks. The model predicts LEGITIMATE on these, creating
# genuine label noise because the phishing intent cannot be detected from text.

HARD_PHISHING_TEMPLATES = [
    "Hey {name},\\n\\nDid you get a chance to check the {project} staging environment? I noticed some unusual behavior earlier but I may have just been seeing things. Let me know if anything looks off on your end.\\n\\n{colleague}",
    "Hi {name},\\n\\nMeeting notes from this morning\'s standup are in the shared drive. Main action items: {colleague} is on deck for the {project} documentation review, and you\'re handling the integration testing sign-off.\\n\\n-- {colleague}",
    "Hey {name}, quick question -- do you know who owns the {project} access configuration? I\'m trying to figure out the right person to ask about some legacy permissions that need updating.\\n\\nThanks,\\n{colleague}",
    "Hello {name},\\n\\nWe\'ll be performing routine maintenance on the {project} file server this Saturday, {date}, from 8 AM to 12 PM. Access to shared drives will be unavailable during this window.\\n\\nIT Operations",
    "Hi {name},\\n\\nYour VPN certificate has been renewed and will take effect on {date}. No action needed on your end -- the update will apply automatically on your next login.\\n\\nIT Security",
    "Hey {name}, I pushed a fix to the {project} staging environment. Can you do a quick sanity check before we promote to production? Want a second pair of eyes on the auth flow.\\n\\nThanks,\\n{colleague}",
    "Hi {name},\\n\\nSharing the Q3 planning spreadsheet for the {project} team as discussed. I\'ve granted you edit access -- let me know if anything in the forecasting section looks wrong to you.\\n\\nCheers,\\n{colleague}",
    "Dear {name},\\n\\nYour annual performance review is scheduled for {date} at 10 AM. Please complete the self-assessment form at least 48 hours in advance and note any {project} milestones you\'d like discussed.\\n\\nPeople Operations",
    "Hi {name},\\n\\nI\'d like to reschedule our sync on the {project} architecture from Tuesday to {date} at 3 PM if that works for you. Same agenda -- just want to include {colleague} who was unavailable earlier.\\n\\nThanks,\\n{colleague}",
    "Hello {name},\\n\\nThis is an invitation for the Q4 planning session for the {project} team on {date} at 10 AM. Please bring your current status summary and any blockers for the roadmap discussion.\\n\\nSee you there,\\n{colleague}",
    "Hi {name},\\n\\nHere\'s your weekly {project} team digest for the week of {date}:\\n\\n- 3 new issues posted for review\\n- Incident postmortem from last Tuesday is ready\\n- {colleague} has updated the onboarding checklist\\n\\nHave a great weekend!\\n{colleague}",
    "Dear {name},\\n\\nOpen enrollment for the 2025 benefits package begins on {date}. You have until the end of the month to make your selections in the HR portal. Reach out to {colleague} if you have questions.\\n\\nHuman Resources",
    "Hi {name},\\n\\nI\'ve updated the new employee onboarding checklist in the {project} shared drive. Can you take a look and flag anything that\'s missing before our next hire joins on {date}?\\n\\n{colleague}",
    "Hi {name},\\n\\nJust confirming receipt of the {project} documentation you sent over. I\'ll review it by EOD {date} and send you feedback before the team presentation.\\n\\n{colleague}",
    "Good morning {name},\\n\\nThe updated security hardening guide for the {project} infrastructure is now live in the shared drive. We\'ve covered certificate rotation and the new access management practices.\\n\\n{colleague}",
    "Hello {name},\\n\\nYour order has shipped and is on track for delivery on {date}. You can track it using the tracking number from your original confirmation email.\\n\\nCustomer Success",
    "Dear {name},\\n\\nReminder from IT that your network password expires in 7 days. Please update it via the employee portal before {date} to avoid any access disruption.\\n\\nIT Help Desk",
    "Hi {name},\\n\\nYour support ticket for the {project} CSV export issue has been resolved. The fix was deployed to production on {date}. Please verify and close the ticket if everything looks good.\\n\\nSupport Team",
    "Hey {name},\\n\\nHope you don\'t mind the reach-out -- {colleague} mentioned you\'re the person to talk to about the {project} data pipeline. I\'m working on something in a similar space and had a couple of questions. Would you have 15 minutes?\\n\\n{colleague}",
    "Hi {name},\\n\\nFYI -- the {project} CI/CD pipeline will be down for maintenance tonight from 11 PM to 1 AM. Please push any critical changes before 10 PM to avoid losing work.\\n\\nThanks,\\n{colleague}",
]'''

# ── New HARD_LEGITIMATE_TEMPLATES ──────────────────────────────────────────────
# Uses the EXACT vocabulary of standard phishing templates (account suspended,
# password must be reset, invoice overdue, limited time offer) but is genuinely
# legitimate. The model predicts PHISHING on these, creating genuine misclassifications.
NEW_HL = '''# ── Hard / ambiguous legitimate templates (label=0) ──────────────────────────
# Real vendor / IT emails that use the EXACT vocabulary of the standard phishing
# templates: account suspended, password expires, invoice overdue, verify identity,
# limited time, competitors. The model predicts PHISHING on these, creating genuine
# label noise because the phishing vocabulary is present in a legitimate context.

HARD_LEGITIMATE_TEMPLATES = [
    "Dear {name},\\n\\nYour {sender_co} account for {company} has been temporarily suspended due to an unpaid invoice. To restore access to {product}, please process Invoice #{invoice} for ${amount} through our payment portal immediately.\\n\\n{sender}\\nAccounts, {sender_co}",
    "Dear {name},\\n\\nWe detected unusual activity on your {company} account with {sender_co} -- a login attempt from an unrecognized device on {date}. To protect your account, please verify your identity through our secure portal.\\n\\nSecurity Team, {sender_co}",
    "Dear {name},\\n\\nYour {company} password for the {sender_co} platform must be reset immediately. We detected a potential credential exposure that may affect your login. Reset now to secure your account.\\n\\nIT Security, {sender_co}",
    "Dear {name},\\n\\nFinal notice: Invoice #{invoice} for ${amount} issued to {company} by {sender_co} is now 30 days overdue. Failure to pay by {date} will result in service suspension and referral to collections.\\n\\n{sender}\\nAccounts Receivable, {sender_co}",
    "Dear {name},\\n\\nYour {sender_co} software license for {product} expires at midnight on {date}. After expiration, the software will stop functioning. Please renew immediately through the customer portal to avoid data loss.\\n\\nLicensing Team, {sender_co}",
    "Dear {name},\\n\\nYour {company} Microsoft 365 subscription is set to expire on {date}. All access to Office applications, OneDrive, and Teams will be suspended after that date. Please renew now to avoid disruption.\\n\\nMicrosoft Account Team",
    "Dear {name},\\n\\nAs a compliance requirement, all {position} accounts at {company} must complete identity verification by {date}. Failure to verify will result in access restrictions. Please log in and complete the verification process now.\\n\\n{sender_co} Compliance",
    "Hi {name},\\n\\nI\'ve been trying to reach you -- our {deadline} discount offer for {company} expires at midnight. You\'d be locking in {discount} off our {product} for the next 12 months. Only {spots} slots remain at this price.\\n\\n{sender}, {sender_co}",
    "Dear {name},\\n\\nThis is a final notice that your {sender_co} account will be permanently deleted on {date} unless you log in to confirm continued use. All associated data for {company} will be irretrievably lost after deletion.\\n\\n{sender_co} Data Operations",
    "Hi {name},\\n\\nI\'ve been trying to reach you about {company}\'s {product} contract. Your competitor in the same sector finalized their renewal yesterday. You have a narrow window before our pricing changes -- this offer expires {deadline}.\\n\\n{sender}, {sender_co}",
    "Dear {name},\\n\\nThis is a confirmation that your scheduled wire transfer of ${amount} to the {sender_co} vendor account has been processed. If you did not authorize this transfer, please contact our fraud line immediately.\\n\\n{sender_co} Payments",
    "Dear {name},\\n\\nYour {company} account with {sender_co} shows unusual API activity on {date} -- ${amount} in unexpected usage charges. We\'ve paused your account to prevent further charges. To restore access, please verify your billing information.\\n\\n{sender_co} Support",
    "Dear {name},\\n\\nAs {position} at {company}, you are required to complete the mandatory information security training by {date}. Failure to comply will result in system access being revoked until training is completed. Log in now.\\n\\nCompliance and Risk, {sender_co}",
    "Hi {name},\\n\\nBased on {company}\'s current {product} usage, our models project you\'ll exceed your plan limits by {date}. This will trigger automatic overage charges of ${amount}. Upgrade now to lock in better rates.\\n\\n{sender}, {sender_co}",
    "Dear {name},\\n\\nYour {product} subscription for {company} will automatically renew on {date} for ${amount}. To cancel or modify your subscription before the renewal date, log in to your account now.\\n\\n{sender_co} Billing",
    "Dear {name},\\n\\nYour {company} data on {sender_co} has not been backed up in over 90 days, putting you at risk of permanent data loss. To restore automated backups and protect your data, please log in and update your configuration immediately.\\n\\n{sender_co} Security",
    "Hi {name},\\n\\nROI snapshot for {company}: companies similar to yours using our {product} see a 40% reduction in costs within 60 days. Only {spots} spots remain for our next cohort, which starts {date}. Reply now to secure your place.\\n\\n{sender}, {sender_co}",
    "Dear {name},\\n\\nYour {sender_co} business account requires annual verification. Please complete the verification process within 48 hours to confirm your {company} account details and avoid suspension.\\n\\n{sender_co} Account Services",
    "Dear {name},\\n\\nPayment of ${amount} is now overdue on your {company} contract with {sender_co}. This is our third and final notice. Please process payment through our online portal or contact {sender} directly to arrange an alternative.\\n\\n{sender_co} Finance",
    "Hi {name},\\n\\nAs {position} at {company}, you qualify for our exclusive {product} pilot program. Only {spots} pilot slots are available -- participants receive 6 months free and priority support. This invitation expires {deadline}. Reply to secure your spot.\\n\\n{sender}, {sender_co}",
]'''

# Replace HARD_PHISHING_TEMPLATES block
text = re.sub(
    r'# ── Hard / ambiguous phishing templates.*?^HARD_PHISHING_TEMPLATES\s*=\s*\[.*?^\]',
    NEW_HP,
    text,
    flags=re.DOTALL | re.MULTILINE,
)

# Replace HARD_LEGITIMATE_TEMPLATES block
text = re.sub(
    r'# ── Hard / ambiguous legitimate templates.*?^HARD_LEGITIMATE_TEMPLATES\s*=\s*\[.*?^\]',
    NEW_HL,
    text,
    flags=re.DOTALL | re.MULTILINE,
)

# Update gen_hard_legitimate to add deadline and discount kwargs
OLD_GEN_HL = """def gen_hard_legitimate() -> str:
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
    )"""

NEW_GEN_HL = """def gen_hard_legitimate() -> str:
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
        deadline=random.choice(DEADLINES),
        discount=random.choice(DISCOUNTS),
        spots=random.choice(SPOTS),
        invoice=str(random.randint(10000, 99999)),
        amount=str(random.randint(500, 50000)),
    )"""

text = text.replace(OLD_GEN_HL, NEW_GEN_HL)

SRC.write_text(text, encoding="utf-8")
print("Patched successfully.")
print(f"HARD_PHISHING_TEMPLATES present: {'HARD_PHISHING_TEMPLATES' in text}")
print(f"HARD_LEGITIMATE_TEMPLATES present: {'HARD_LEGITIMATE_TEMPLATES' in text}")
print(f"deadline in gen_hard_legitimate: {'deadline=random.choice(DEADLINES)' in text}")
