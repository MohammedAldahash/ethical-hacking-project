// data/_generate_helper.mjs
// Calls the ICS-442 tool's generateEmail() to produce phishing samples.
// Run from the phishing-detector/ directory so relative imports resolve correctly.

import { generateEmail } from "../lib/llm.js";

const args = JSON.parse(process.argv[2]);

const targetInfo = {
  name: args.targetName,
  position: args.targetPosition,
  company: args.targetCompany,
  industry: args.industry || "",
  painPoint: args.painPoint || "",
};

const senderInfo = {
  name: args.senderName,
  company: args.senderCompany,
  product: args.product,
  valueProps: args.valueProps || "saves time, reduces costs",
  cta: args.cta || "Schedule a 15-minute demo",
};

try {
  const result = await generateEmail(targetInfo, senderInfo, args.tone);
  console.log(JSON.stringify(result));
} catch (err) {
  console.error(JSON.stringify({ error: err.message }));
  process.exit(1);
}
