#!/usr/bin/env node
// index.js — Main entry point for email-campaign CLI

import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

// Load .env from project root before anything else
const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = join(__dirname, ".env");
if (existsSync(envPath)) {
  const envContent = readFileSync(envPath, "utf-8");
  for (const line of envContent.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIndex = trimmed.indexOf("=");
    if (eqIndex === -1) continue;
    const key = trimmed.slice(0, eqIndex).trim();
    const value = trimmed.slice(eqIndex + 1).trim().replace(/^["']|["']$/g, "");
    if (!process.env[key]) process.env[key] = value;
  }
}

import { Command } from "commander";
import chalk from "chalk";
import { runCompose } from "./commands/compose.js";
import { runManageLists } from "./commands/manage-lists.js";

const program = new Command();

program
  .name("email-campaign")
  .description(
    chalk.bold("AI-powered email campaign CLI") +
      "\n  Craft personalized sales emails using Claude and send them at scale."
  )
  .version("1.0.0");

// ─── compose command ───────────────────────────────────────────────────────
program
  .command("compose")
  .description("Create and send an AI-generated email campaign")
  .option("--dry-run", "Generate and preview the email without actually sending")
  .action(async (options) => {
    try {
      await runCompose({ dryRun: options.dryRun });
    } catch (err) {
      console.error(chalk.red("\n✗ Unexpected error:"), err.message);
      if (process.env.DEBUG) console.error(err.stack);
      process.exit(1);
    }
  });

// ─── lists command ─────────────────────────────────────────────────────────
program
  .command("lists")
  .description("Manage saved recipient lists")
  .action(async () => {
    try {
      await runManageLists();
    } catch (err) {
      console.error(chalk.red("\n✗ Unexpected error:"), err.message);
      process.exit(1);
    }
  });

// ─── setup command ─────────────────────────────────────────────────────────
program
  .command("setup")
  .description("Interactive setup wizard — configure API keys and SMTP")
  .action(async () => {
    const { default: inquirer } = await import("inquirer");
    const { writeFileSync } = await import("fs");

    console.log(chalk.bold.cyan("\n  ⚙  Setup Wizard\n"));
    console.log(
      chalk.gray("  This will create a .env file with your credentials.\n")
    );

    console.log(chalk.cyan("  Get your FREE Groq API key at: https://console.groq.com\n"));

    const answers = await inquirer.prompt([
      {
        type: "password",
        name: "groqKey",
        message: "Groq API Key (free at console.groq.com):",
        mask: "*",
        validate: (v) => v.trim().length > 0 || "Required",
      },
      {
        type: "input",
        name: "smtpHost",
        message: "SMTP Host:",
        default: "smtp.gmail.com",
      },
      {
        type: "input",
        name: "smtpPort",
        message: "SMTP Port:",
        default: "587",
      },
      {
        type: "input",
        name: "smtpUser",
        message: "SMTP Email (your email address):",
        validate: (v) => v.includes("@") || "Must be a valid email",
      },
      {
        type: "password",
        name: "smtpPass",
        message: "SMTP Password / App Password:",
        mask: "*",
        validate: (v) => v.trim().length > 0 || "Required",
      },
      {
        type: "input",
        name: "fromName",
        message: "Your display name (shown to recipients):",
        validate: (v) => v.trim().length > 0 || "Required",
      },
    ]);

    const envContent = `# Groq API Key (FREE — https://console.groq.com)
GROQ_API_KEY=${answers.groqKey}

# Email SMTP Settings
SMTP_HOST=${answers.smtpHost}
SMTP_PORT=${answers.smtpPort}
SMTP_USER=${answers.smtpUser}
SMTP_PASS=${answers.smtpPass}
SMTP_FROM_NAME=${answers.fromName}
`;

    writeFileSync(join(__dirname, ".env"), envContent, "utf-8");
    console.log(chalk.green("\n✓ .env file created successfully!"));
    console.log(
      chalk.cyan(
        '\n  Run  email-campaign compose  to start your first campaign!\n'
      )
    );
  });

// ─── Default: show help ────────────────────────────────────────────────────
if (process.argv.length <= 2) {
  console.log(chalk.bold.magenta("\n  ✉  AI Email Campaign CLI\n"));
  console.log(
    chalk.white("  Commands:\n")
  );
  console.log(
    `  ${chalk.cyan("compose")}      — ${chalk.gray("Create and send an AI-powered campaign")}`
  );
  console.log(
    `  ${chalk.cyan("compose --dry-run")} — ${chalk.gray("Preview without sending")}`
  );
  console.log(
    `  ${chalk.cyan("lists")}        — ${chalk.gray("Manage saved recipient lists")}`
  );
  console.log(
    `  ${chalk.cyan("setup")}        — ${chalk.gray("Configure API keys and SMTP settings")}`
  );
  console.log(
    `  ${chalk.cyan("--help")}       — ${chalk.gray("Show full help\n")}`
  );
  process.exit(0);
}

program.parse();
