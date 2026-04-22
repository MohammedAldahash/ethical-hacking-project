// commands/compose.js
// Interactive prompts to gather info, generate email, and queue sending

import inquirer from "inquirer";
import chalk from "chalk";
import ora from "ora";
import { generateEmail } from "../lib/llm.js";
import { TONE_CHOICES, TONES } from "../lib/tones.js";
import {
  getAllLists,
  getList,
  saveList,
  parseEmailInput,
  validateEmails,
  listNames,
} from "../lib/recipients.js";
import { sendBulkEmails, verifyConnection } from "../lib/emailSender.js";

const DIVIDER = chalk.gray("─".repeat(60));

function header(title) {
  console.log("\n" + DIVIDER);
  console.log(chalk.bold.cyan(`  ${title}`));
  console.log(DIVIDER);
}

function printEmailPreview(subject, body) {
  console.log("\n" + chalk.bgWhite.black("  EMAIL PREVIEW  ") + "\n");
  console.log(chalk.bold("Subject: ") + chalk.yellow(subject));
  console.log(DIVIDER);
  console.log(chalk.white(body));
  console.log(DIVIDER);
}

export async function runCompose({ dryRun = false } = {}) {
  console.log(
    chalk.bold.magenta("\n  ✉  AI Email Campaign CLI") +
      chalk.gray("  v1.0.0") +
      (dryRun ? chalk.yellow("  [DRY RUN]") : "")
  );
  console.log(
    chalk.gray("  Powered by Claude · Let's craft something irresistible.\n")
  );

  // ─── STEP 1: Sender Info ───────────────────────────────────────
  header("STEP 1 of 4 · About You");

  const sender = await inquirer.prompt([
    {
      type: "input",
      name: "name",
      message: "Your full name:",
      validate: (v) => v.trim().length > 0 || "Name is required",
    },
    {
      type: "input",
      name: "company",
      message: "Your company name:",
      validate: (v) => v.trim().length > 0 || "Company is required",
    },
    {
      type: "input",
      name: "product",
      message: "What product or service are you selling?",
      validate: (v) => v.trim().length > 0 || "Product/service is required",
    },
    {
      type: "input",
      name: "valueProps",
      message: "Key value propositions (comma-separated):",
      default: "saves time, reduces costs, easy to integrate",
    },
    {
      type: "input",
      name: "cta",
      message: "Call to action:",
      default: "Schedule a free 15-minute demo",
    },
  ]);

  // ─── STEP 2: Target Info ───────────────────────────────────────
  header("STEP 2 of 4 · About Your Target");

  const target = await inquirer.prompt([
    {
      type: "input",
      name: "name",
      message: "Recipient's first name (used for personalization):",
      default: "there",
    },
    {
      type: "input",
      name: "position",
      message: "Recipient's job title / position:",
      default: "Decision Maker",
    },
    {
      type: "input",
      name: "company",
      message: "Recipient's company name:",
      default: "their company",
    },
    {
      type: "input",
      name: "industry",
      message: "Industry (optional, helps personalization):",
      default: "",
    },
    {
      type: "input",
      name: "painPoint",
      message: "Known pain point or reason for outreach (optional):",
      default: "",
    },
  ]);

  // ─── STEP 3: Tone ──────────────────────────────────────────────
  header("STEP 3 of 4 · Email Tone");

  const { tone } = await inquirer.prompt([
    {
      type: "list",
      name: "tone",
      message: "Choose the tone for your email:",
      choices: TONE_CHOICES,
    },
  ]);

  // ─── Generate Email ────────────────────────────────────────────
  console.log();
  const spinner = ora({
    text: chalk.cyan("Generating your email with Claude..."),
    spinner: "dots",
  }).start();

  let email;
  try {
    email = await generateEmail(target, sender, tone);
    spinner.succeed(chalk.green("Email generated!"));
  } catch (err) {
    spinner.fail(chalk.red("Failed to generate email"));
    console.error(chalk.red(err.message));
    process.exit(1);
  }

  // Show preview
  printEmailPreview(email.subject, email.body);

  // Allow regeneration with different tone or approve
  let approved = false;
  let currentEmail = email;
  let currentTone = tone;

  while (!approved) {
    const { action } = await inquirer.prompt([
      {
        type: "list",
        name: "action",
        message: "What would you like to do?",
        choices: [
          { name: "✅  Looks great — proceed to recipients", value: "approve" },
          { name: "🔄  Regenerate with same tone", value: "regen" },
          { name: "🎨  Change tone & regenerate", value: "change_tone" },
          { name: "✏️   Edit subject line manually", value: "edit_subject" },
          { name: "❌  Cancel and exit", value: "cancel" },
        ],
      },
    ]);

    if (action === "approve") {
      approved = true;
    } else if (action === "cancel") {
      console.log(chalk.yellow("\nCampaign cancelled.\n"));
      process.exit(0);
    } else if (action === "edit_subject") {
      const { newSubject } = await inquirer.prompt([
        {
          type: "input",
          name: "newSubject",
          message: "Enter new subject line:",
          default: currentEmail.subject,
        },
      ]);
      currentEmail = { ...currentEmail, subject: newSubject };
      printEmailPreview(currentEmail.subject, currentEmail.body);
    } else if (action === "change_tone") {
      const { newTone } = await inquirer.prompt([
        {
          type: "list",
          name: "newTone",
          message: "Choose a new tone:",
          choices: TONE_CHOICES.filter((c) => c.value !== currentTone),
        },
      ]);
      currentTone = newTone;
      const regenSpinner = ora(
        chalk.cyan(`Regenerating with ${TONES[newTone].label} tone...`)
      ).start();
      try {
        currentEmail = await generateEmail(target, sender, newTone);
        regenSpinner.succeed(chalk.green("Email regenerated!"));
      } catch (err) {
        regenSpinner.fail(chalk.red("Failed"));
        console.error(chalk.red(err.message));
      }
      printEmailPreview(currentEmail.subject, currentEmail.body);
    } else if (action === "regen") {
      const regenSpinner = ora(chalk.cyan("Regenerating...")).start();
      try {
        currentEmail = await generateEmail(target, sender, currentTone);
        regenSpinner.succeed(chalk.green("Email regenerated!"));
      } catch (err) {
        regenSpinner.fail(chalk.red("Failed"));
      }
      printEmailPreview(currentEmail.subject, currentEmail.body);
    }
  }

  // ─── STEP 4: Recipients ────────────────────────────────────────
  header("STEP 4 of 4 · Select Recipients");

  const savedLists = listNames();

  const { recipientSource } = await inquirer.prompt([
    {
      type: "list",
      name: "recipientSource",
      message: "How would you like to provide recipients?",
      choices: [
        { name: "📋  Enter email addresses manually", value: "manual" },
        ...(savedLists.length > 0
          ? [{ name: "💾  Load a saved recipient list", value: "saved" }]
          : []),
        { name: "➕  Enter emails and save as new list", value: "save_new" },
      ],
    },
  ]);

  let recipients = [];

  if (recipientSource === "manual" || recipientSource === "save_new") {
    const { emailInput } = await inquirer.prompt([
      {
        type: "editor",
        name: "emailInput",
        message:
          "Enter email addresses (one per line or comma-separated) — your editor will open:",
        default: "recipient@example.com\n",
        waitForUserInput: false,
      },
    ]);

    recipients = parseEmailInput(emailInput);
    const { valid, invalid } = validateEmails(recipients);

    if (invalid.length > 0) {
      console.log(chalk.yellow(`\n⚠  Skipping ${invalid.length} invalid email(s):`));
      invalid.forEach((e) => console.log(chalk.gray(`   • ${e}`)));
    }

    recipients = valid;

    if (recipientSource === "save_new" && recipients.length > 0) {
      const { listName } = await inquirer.prompt([
        {
          type: "input",
          name: "listName",
          message: "Save this list as:",
          validate: (v) => v.trim().length > 0 || "Name required",
        },
      ]);
      saveList(listName, recipients);
      console.log(chalk.green(`✓  List "${listName}" saved with ${recipients.length} contacts.`));
    }
  } else if (recipientSource === "saved") {
    const { listName } = await inquirer.prompt([
      {
        type: "list",
        name: "listName",
        message: "Select a saved list:",
        choices: savedLists.map((name) => {
          const emails = getList(name);
          return {
            name: `${name} (${emails.length} contacts)`,
            value: name,
          };
        }),
      },
    ]);
    recipients = getList(listName);
    console.log(
      chalk.green(`✓  Loaded ${recipients.length} contacts from "${listName}"`)
    );
  }

  if (recipients.length === 0) {
    console.log(chalk.red("\n✗ No valid recipients. Campaign cancelled.\n"));
    process.exit(1);
  }

  // ─── Confirm & Send ────────────────────────────────────────────
  console.log("\n" + DIVIDER);
  console.log(chalk.bold("  📬 Campaign Summary\n"));
  console.log(`  ${chalk.bold("Subject:")}  ${chalk.yellow(currentEmail.subject)}`);
  console.log(`  ${chalk.bold("Tone:")}     ${TONES[currentTone].label}`);
  console.log(`  ${chalk.bold("From:")}     ${sender.name} at ${sender.company}`);
  console.log(
    `  ${chalk.bold("To:")}       ${chalk.cyan(recipients.length)} recipient(s)`
  );
  recipients.forEach((r) => console.log(chalk.gray(`             • ${r}`)));
  if (dryRun) {
    console.log(chalk.yellow("\n  ⚡ DRY RUN MODE — emails will NOT be sent"));
  }
  console.log(DIVIDER + "\n");

  const { confirmed } = await inquirer.prompt([
    {
      type: "confirm",
      name: "confirmed",
      message: dryRun
        ? `Simulate sending to ${recipients.length} recipient(s)?`
        : `Send to ${recipients.length} recipient(s) now?`,
      default: false,
    },
  ]);

  if (!confirmed) {
    console.log(chalk.yellow("\nCampaign cancelled by user.\n"));
    process.exit(0);
  }

  if (dryRun) {
    console.log(chalk.yellow("\n🧪 DRY RUN — Simulating send...\n"));
    recipients.forEach((r) => {
      console.log(chalk.green(`  ✓ [DRY RUN] Would send to: ${r}`));
    });
    console.log(
      chalk.bold.green(`\n  ✅ Dry run complete! ${recipients.length} emails would be sent.\n`)
    );
    return;
  }

  // ─── Verify SMTP & Send ────────────────────────────────────────
  const verifySpinner = ora(chalk.cyan("Verifying SMTP connection...")).start();
  try {
    await verifyConnection();
    verifySpinner.succeed(chalk.green("SMTP connection verified"));
  } catch (err) {
    verifySpinner.fail(chalk.red("SMTP connection failed"));
    console.error(chalk.red(err.message));
    console.log(
      chalk.yellow("\nTip: Check your SMTP settings in .env file.\n")
    );
    process.exit(1);
  }

  console.log();
  const sendSpinner = ora(chalk.cyan(`Sending to ${recipients.length} recipients...`)).start();

  const { sent, failed, results } = await sendBulkEmails(
    recipients,
    currentEmail,
    sender.name,
    (i, total, result) => {
      if (result.success) {
        sendSpinner.text = chalk.cyan(
          `Sending... (${i}/${total}) ✓ ${result.email}`
        );
      } else {
        sendSpinner.text = chalk.cyan(
          `Sending... (${i}/${total}) ✗ ${result.email}`
        );
      }
    }
  );

  if (failed === 0) {
    sendSpinner.succeed(
      chalk.bold.green(`✅ All ${sent} emails sent successfully!`)
    );
  } else {
    sendSpinner.warn(
      chalk.yellow(`Sent: ${sent} ✓  Failed: ${failed} ✗`)
    );
  }

  // Show failures
  const failures = results.filter((r) => !r.success);
  if (failures.length > 0) {
    console.log(chalk.red("\n  Failed recipients:"));
    failures.forEach((f) => {
      console.log(chalk.red(`  • ${f.email}: ${f.error}`));
    });
  }

  console.log(chalk.gray("\n  Campaign complete. Have a great day! 👋\n"));
}
