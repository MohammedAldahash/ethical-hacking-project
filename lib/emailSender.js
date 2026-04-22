// lib/emailSender.js
// Handles SMTP email sending via nodemailer

import nodemailer from "nodemailer";

let transporter;

function getTransporter() {
  if (!transporter) {
    const required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"];
    const missing = required.filter((k) => !process.env[k]);
    if (missing.length > 0) {
      throw new Error(
        `Missing SMTP config in .env: ${missing.join(", ")}\nSee .env.example for setup instructions.`
      );
    }

    transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: parseInt(process.env.SMTP_PORT, 10),
      secure: parseInt(process.env.SMTP_PORT, 10) === 465,
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
      },
    });
  }
  return transporter;
}

/**
 * Send a single email
 * @param {Object} opts
 * @param {string} opts.to - Recipient email
 * @param {string} opts.subject - Email subject
 * @param {string} opts.body - Email body (plain text with \n line breaks)
 * @param {string} opts.fromName - Sender display name
 * @returns {Promise<{success: boolean, email: string, error?: string}>}
 */
export async function sendEmail({ to, subject, body, fromName }) {
  const transport = getTransporter();
  const fromAddress = process.env.SMTP_USER;
  const displayName = fromName || process.env.SMTP_FROM_NAME || fromAddress;

  try {
    await transport.sendMail({
      from: `"${displayName}" <${fromAddress}>`,
      to,
      subject,
      text: body,
      html: bodyToHtml(body),
    });
    return { success: true, email: to };
  } catch (err) {
    return { success: false, email: to, error: err.message };
  }
}

/**
 * Send emails to a list of recipients with a small delay between sends
 * @param {string[]} recipients - List of email addresses
 * @param {Object} emailContent - { subject, body }
 * @param {string} fromName - Sender name
 * @param {Function} onProgress - Callback(sent, total, result)
 * @returns {Promise<{sent: number, failed: number, results: Array}>}
 */
export async function sendBulkEmails(
  recipients,
  emailContent,
  fromName,
  onProgress
) {
  const results = [];
  let sent = 0;
  let failed = 0;

  for (let i = 0; i < recipients.length; i++) {
    const to = recipients[i].trim();
    if (!to) continue;

    const result = await sendEmail({
      to,
      subject: emailContent.subject,
      body: emailContent.body,
      fromName,
    });

    results.push(result);
    if (result.success) {
      sent++;
    } else {
      failed++;
    }

    if (onProgress) {
      onProgress(i + 1, recipients.length, result);
    }

    // Small delay to avoid rate limiting
    if (i < recipients.length - 1) {
      await sleep(300);
    }
  }

  return { sent, failed, results };
}

/**
 * Verify SMTP connection
 */
export async function verifyConnection() {
  const transport = getTransporter();
  await transport.verify();
}

// Convert plain text body to simple HTML
function bodyToHtml(text) {
  return `<div style="font-family: Arial, sans-serif; font-size: 15px; line-height: 1.6; color: #333; max-width: 600px;">
    ${text
      .split("\n")
      .map((line) =>
        line.trim() === "" ? "<br>" : `<p style="margin:0 0 8px 0">${line}</p>`
      )
      .join("")}
  </div>`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
