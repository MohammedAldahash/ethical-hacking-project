# ✉ AI Email Campaign CLI
### 100% Free · Powered by Groq + Gmail

A command-line tool that uses AI to write personalized sales emails and send them via Gmail — completely free, no credit card required.

---

## What You Need (All Free)

| Requirement | Where to get it | Cost |
|---|---|---|
| Node.js v18+ | https://nodejs.org | Free |
| Groq API Key | https://console.groq.com | Free |
| Gmail account | https://gmail.com | Free |
| Gmail App Password | Google Account settings | Free |

---

## Step-by-Step Setup Guide

### Step 1 — Install Node.js
If you don't have Node.js installed:
- Go to https://nodejs.org
- Download and install the **LTS version**
- Verify by running: `node --version` (should show v18 or higher)

---

### Step 2 — Get Your Free Groq API Key
Groq is a free AI service — no credit card needed.

1. Go to **https://console.groq.com**
2. Click **Sign Up** and create a free account
3. Once logged in, go to **API Keys** in the left sidebar
4. Click **Create API Key**
5. Give it a name like `email-campaign`
6. **Copy the key** — you'll need it in Step 5

---

### Step 3 — Set Up Gmail App Password
Gmail requires an "App Password" for third-party tools (more secure than your real password).

1. Go to your **Google Account** → https://myaccount.google.com
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", enable **2-Step Verification** (if not already on)
4. Go back to Security, scroll down and click **App passwords**
   - Direct link: https://myaccount.google.com/apppasswords
5. Under "Select app", choose **Mail**
6. Under "Select device", choose **Other** and type `email-campaign`
7. Click **Generate**
8. **Copy the 16-character password** shown — you'll need it in Step 5

> ⚠️ If you don't see "App passwords", make sure 2-Step Verification is turned ON first.

---

### Step 4 — Download & Install the Tool

```bash
# Create a folder for the project
mkdir email-campaign-cli
cd email-campaign-cli

# Place all the downloaded files in this folder, then install dependencies
npm install
```

Your folder should look like this:
```
email-campaign-cli/
├── index.js
├── package.json
├── .env.example
├── README.md
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

### Step 5 — Configure Your Keys (Setup Wizard)

Run the interactive setup wizard:

```bash
node index.js setup
```

It will ask you for:
- **Groq API Key** → paste the key from Step 2
- **SMTP Host** → press Enter to keep `smtp.gmail.com`
- **SMTP Port** → press Enter to keep `587`
- **SMTP Email** → your Gmail address (e.g. `you@gmail.com`)
- **SMTP Password** → paste the 16-character App Password from Step 3
- **Display Name** → your name as it will appear to recipients

This creates a `.env` file in your project folder with all your settings saved.

---

### Step 6 — Run Your First Campaign

```bash
node index.js compose
```

You'll be guided through 4 steps:

1. **About You** — your name, company, product, value propositions
2. **About the Target** — recipient name, job title, company, pain points
3. **Choose Tone** — 6 options (Cold, Urgent, Excited, Warm, Formal, Casual)
4. **Select Recipients** — enter emails manually or load a saved list

---

## All Available Commands

```bash
# Start a campaign
node index.js compose

# Preview without sending (safe for testing)
node index.js compose --dry-run

# Manage saved contact lists
node index.js lists

# Re-run the setup wizard
node index.js setup

# Show help
node index.js --help
```

---

## Email Tones

| Tone | Best for |
|---|---|
| 🧊 Cold & Professional | First outreach to executives |
| 🔥 Urgent & Time-Sensitive | Limited-time offers, deadlines |
| 🚀 Excited & Enthusiastic | Product launches, big news |
| 🤝 Warm & Friendly | Relationship-building, warm leads |
| 🎩 Formal & Corporate | Enterprise, legal, finance sectors |
| 😎 Casual & Conversational | Startups, tech, creative industries |

---

## Managing Recipient Lists

You can save groups of emails as named lists for reuse:

```bash
node index.js lists
```

Options:
- **Create** a new list (enter emails one per line)
- **View** a saved list
- **Delete** a list

Lists are stored in `data/recipients.json` on your machine.

---

## Troubleshooting

**"GROQ_API_KEY is not set"**
→ Run `node index.js setup` and enter your Groq key, or manually create a `.env` file based on `.env.example`

**"SMTP connection failed"**
→ Double-check your Gmail App Password — it must be the 16-character generated password, NOT your regular Gmail password

**"App passwords" option missing in Google Account**
→ You need to enable 2-Step Verification first under Security settings

**Emails going to spam**
→ Normal for cold outreach. Consider warming up your Gmail account by sending a few manual emails first.

**"No valid recipients"**
→ Make sure email addresses are valid and separated by commas or new lines

---

## Privacy & Security

- Your `.env` file contains sensitive keys — never share it or commit it to Git
- Add `.env` to your `.gitignore` if using version control
- Groq does not store your prompts permanently (see their privacy policy)
- Emails are sent directly from your Gmail account

---

## Free Tier Limits

| Service | Free Limit |
|---|---|
| Groq API | ~14,400 requests/day (very generous) |
| Gmail SMTP | 500 emails/day |

For most use cases, these limits are more than sufficient.
