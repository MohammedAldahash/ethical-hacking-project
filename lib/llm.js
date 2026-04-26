// lib/llm.js
// Wrapper around the Groq API for email generation (free tier)

import Groq from "groq-sdk";
import { TONES } from "./tones.js";

let client;

function getClient() {
  if (!client) {
    if (!process.env.GROQ_API_KEY) {
      throw new Error(
        "GROQ_API_KEY is not set.\n\n" +
        "  1. Sign up free at https://console.groq.com\n" +
        "  2. Create an API key (no credit card needed)\n" +
        "  3. Run: node index.js setup\n"
      );
    }
    client = new Groq({ apiKey: process.env.GROQ_API_KEY });
  }
  return client;
}

/**
 * Generate a phishing email using Groq (llama3-70b)
 * @param {Object} targetInfo - Info about the recipient
 * @param {Object} senderInfo - Info about the sender
 * @param {string} tone - Tone key from TONES
 * @returns {Promise<{subject: string, body: string}>}
 */
export async function generateEmail(targetInfo, senderInfo, tone) {
  const toneInstruction = TONES[tone]?.instruction || TONES.cold.instruction;

  const prompt = `You are a world-class B2B copywriter who crafts highly personalized, effective sales emails.

Write a phishing email with the following details:

RECIPIENT INFO:
- Name: ${targetInfo.name}
- Position: ${targetInfo.position}
- Company: ${targetInfo.company}
- Industry: ${targetInfo.industry || "Not specified"}
- Pain point or context: ${targetInfo.painPoint || "Not specified"}

SENDER INFO:
- Name: ${senderInfo.name}
- Company: ${senderInfo.company}
- Product/Service: ${senderInfo.product}
- Key value propositions: ${senderInfo.valueProps}
- Call to action: ${senderInfo.cta || "Schedule a 15-minute call"}

TONE INSTRUCTION:
${toneInstruction}

RULES:
- Make it feel genuinely personalized to ${targetInfo.name}'s role and company
- Never use generic filler phrases like "I hope this email finds you well"
- The subject line must be compelling and specific — not generic
- Include exactly ONE clear call to action
- Do NOT use placeholders like [Your Name] — use the actual info provided

Respond with ONLY a valid JSON object (no markdown, no backticks), like this:
{"subject": "...", "body": "..."}

The body should use \\n for line breaks.`;

  const groq = getClient();

  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",  // Free, fast, high quality
    max_tokens: 1024,
    temperature: 0.7,
    messages: [
      {
        role: "system",
        content: "You are an expert sales copywriter. Always respond with valid JSON only — no markdown, no explanation, no backticks.",
      },
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const raw = completion.choices[0].message.content.trim();

  // Strip markdown code fences if model adds them anyway
  const cleaned = raw.replace(/^```(?:json)?\n?/, "").replace(/\n?```$/, "");

  const parsed = JSON.parse(cleaned);

  if (!parsed.subject || !parsed.body) {
    throw new Error("LLM response missing subject or body fields");
  }

  return parsed;
}

/**
 * Regenerate email with a different tone
 */
export async function regenerateWithTone(targetInfo, senderInfo, newTone) {
  return generateEmail(targetInfo, senderInfo, newTone);
}
