// commands/manage-lists.js
// Manage saved recipient lists (view, add, delete)

import inquirer from "inquirer";
import chalk from "chalk";
import {
  getAllLists,
  saveList,
  deleteList,
  listNames,
  parseEmailInput,
  validateEmails,
} from "../lib/recipients.js";

const DIVIDER = chalk.gray("─".repeat(60));

export async function runManageLists() {
  console.log(chalk.bold.cyan("\n  📋 Recipient List Manager\n"));

  let running = true;
  while (running) {
    const lists = getAllLists();
    const names = Object.keys(lists);

    console.log(DIVIDER);
    if (names.length === 0) {
      console.log(chalk.gray("  No saved lists yet.\n"));
    } else {
      console.log(chalk.bold("  Saved Lists:\n"));
      names.forEach((name) => {
        console.log(
          `  ${chalk.cyan("•")} ${chalk.bold(name)} — ${chalk.gray(lists[name].length + " contacts")}`
        );
        lists[name].slice(0, 3).forEach((e) => console.log(chalk.gray(`      ${e}`)));
        if (lists[name].length > 3) {
          console.log(chalk.gray(`      ... and ${lists[name].length - 3} more`));
        }
      });
    }
    console.log();

    const { action } = await inquirer.prompt([
      {
        type: "list",
        name: "action",
        message: "What would you like to do?",
        choices: [
          { name: "➕  Create a new list", value: "create" },
          ...(names.length > 0
            ? [
                { name: "👁   View full list", value: "view" },
                { name: "🗑   Delete a list", value: "delete" },
              ]
            : []),
          { name: "← Back / Exit", value: "exit" },
        ],
      },
    ]);

    if (action === "exit") {
      running = false;
    } else if (action === "create") {
      await createList();
    } else if (action === "view") {
      await viewList(names, lists);
    } else if (action === "delete") {
      await deleteListPrompt(names);
    }
  }

  console.log(chalk.gray("\n  Goodbye!\n"));
}

async function createList() {
  const { listName } = await inquirer.prompt([
    {
      type: "input",
      name: "listName",
      message: "List name:",
      validate: (v) => v.trim().length > 0 || "Name required",
    },
  ]);

  const { emailInput } = await inquirer.prompt([
    {
      type: "editor",
      name: "emailInput",
      message: "Enter emails (one per line or comma-separated):",
      default: "recipient@example.com\n",
      waitForUserInput: false,
    },
  ]);

  const emails = parseEmailInput(emailInput);
  const { valid, invalid } = validateEmails(emails);

  if (invalid.length > 0) {
    console.log(chalk.yellow(`\n⚠  Skipping ${invalid.length} invalid email(s):`));
    invalid.forEach((e) => console.log(chalk.gray(`   • ${e}`)));
  }

  if (valid.length === 0) {
    console.log(chalk.red("✗ No valid emails. List not saved.\n"));
    return;
  }

  saveList(listName, valid);
  console.log(
    chalk.green(`\n✓ List "${listName}" saved with ${valid.length} contacts.\n`)
  );
}

async function viewList(names, lists) {
  const { listName } = await inquirer.prompt([
    {
      type: "list",
      name: "listName",
      message: "Choose a list to view:",
      choices: names,
    },
  ]);

  console.log(chalk.bold(`\n  List: ${listName}\n`));
  lists[listName].forEach((email, i) => {
    console.log(chalk.gray(`  ${i + 1}. ${email}`));
  });
  console.log();
}

async function deleteListPrompt(names) {
  const { listName } = await inquirer.prompt([
    {
      type: "list",
      name: "listName",
      message: "Which list would you like to delete?",
      choices: names,
    },
  ]);

  const { confirmed } = await inquirer.prompt([
    {
      type: "confirm",
      name: "confirmed",
      message: chalk.red(`Are you sure you want to delete "${listName}"?`),
      default: false,
    },
  ]);

  if (confirmed) {
    deleteList(listName);
    console.log(chalk.green(`\n✓ List "${listName}" deleted.\n`));
  } else {
    console.log(chalk.gray("  Deletion cancelled.\n"));
  }
}
