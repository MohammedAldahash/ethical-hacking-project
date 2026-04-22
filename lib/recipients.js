// lib/recipients.js
// Manage saved recipient lists in data/recipients.json

import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_PATH = join(__dirname, "../data/recipients.json");

function loadData() {
  if (!existsSync(DATA_PATH)) {
    return { lists: {} };
  }
  return JSON.parse(readFileSync(DATA_PATH, "utf-8"));
}

function saveData(data) {
  writeFileSync(DATA_PATH, JSON.stringify(data, null, 2), "utf-8");
}

export function getAllLists() {
  const data = loadData();
  return data.lists || {};
}

export function getList(name) {
  const data = loadData();
  return data.lists?.[name] || null;
}

export function saveList(name, emails) {
  const data = loadData();
  data.lists[name] = emails;
  saveData(data);
}

export function deleteList(name) {
  const data = loadData();
  delete data.lists[name];
  saveData(data);
}

export function listNames() {
  return Object.keys(loadData().lists || {});
}

/**
 * Parse a comma/newline separated string of emails into an array
 */
export function parseEmailInput(input) {
  return input
    .split(/[\n,]+/)
    .map((e) => e.trim())
    .filter((e) => e.includes("@"));
}

/**
 * Validate a list of email addresses, return { valid, invalid }
 */
export function validateEmails(emails) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const valid = [];
  const invalid = [];
  for (const email of emails) {
    if (emailRegex.test(email)) {
      valid.push(email);
    } else {
      invalid.push(email);
    }
  }
  return { valid, invalid };
}
