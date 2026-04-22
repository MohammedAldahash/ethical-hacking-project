// lib/tones.js
// Defines all available email tones and their LLM prompt modifiers

export const TONES = {
  cold: {
    label: "🧊  Cold & Professional",
    description: "Direct, data-driven, no fluff",
    instruction: `Write in a cold, professional tone. Be concise and data-driven. 
      Get to the point immediately. Avoid warm language or pleasantries. 
      Focus on ROI, metrics, and business value. Keep it under 150 words.`,
  },
  urgent: {
    label: "🔥  Urgent & Time-Sensitive",
    description: "Creates FOMO, deadline-driven",
    instruction: `Write with strong urgency. Create a sense of FOMO (fear of missing out). 
      Reference limited availability, a deadline, or a time-sensitive opportunity. 
      Use action-oriented language. Make the reader feel they MUST respond now.`,
  },
  excited: {
    label: "🚀  Excited & Enthusiastic",
    description: "High energy, passionate, inspiring",
    instruction: `Write with genuine excitement and enthusiasm. Use energetic, passionate language. 
      Show real excitement about the product/service and what it can do for them. 
      Be upbeat and inspiring. Make the reader feel the energy.`,
  },
  warm: {
    label: "🤝  Warm & Friendly",
    description: "Personal, approachable, relationship-focused",
    instruction: `Write in a warm, friendly tone like reaching out to a colleague. 
      Be personable and human. Reference their specific situation with empathy. 
      Build rapport before pitching. Make them feel understood and valued.`,
  },
  formal: {
    label: "🎩  Formal & Corporate",
    description: "Polished, authoritative, boardroom-ready",
    instruction: `Write in a highly formal, corporate tone. Use formal salutations and closings. 
      Employ sophisticated vocabulary. Structure it like a business proposal. 
      Project authority and credibility. Avoid contractions or casual language.`,
  },
  casual: {
    label: "😎  Casual & Conversational",
    description: "Relaxed, peer-to-peer, no sales-speak",
    instruction: `Write casually, like a peer reaching out to a friend. 
      Use conversational language, maybe even a bit of humor. 
      Avoid sounding salesy. Make it feel like a genuine human conversation. 
      Short sentences, contractions, natural flow.`,
  },
};

export const TONE_CHOICES = Object.entries(TONES).map(([key, val]) => ({
  name: `${val.label}  — ${val.description}`,
  value: key,
}));
