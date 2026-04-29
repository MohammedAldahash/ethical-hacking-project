"""
Core phishing detection engine.
Loads fine-tuned RoBERTa (or falls back to HuggingFace public model).
"""

import re
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

FALLBACK_MODEL = "ealvaradob/bert-finetuned-phishing"

# Trait keyword patterns
TRAIT_PATTERNS = {
    "urgency": [
        r"limited time", r"act now", r"expires?", r"deadline", r"hurry",
        r"don'?t miss", r"only \d+ days?", r"this week only", r"respond (immediately|now|today)",
        r"urgent", r"last chance", r"final notice", r"closing (today|tonight|soon)",
        r"before (midnight|end of (day|week|month))",
    ],
    "social_proof": [
        r"teams? like yours?", r"companies? (similar to|like)", r"industry leaders?",
        r"others have", r"trusted by", r"join \d+", r"\d+ companies?", r"\d+ teams?",
        r"peers?", r"competitors?", r"others? in your (space|sector|industry)",
    ],
    "authority": [
        r"\bCEO\b", r"\bCFO\b", r"\bCTO\b", r"\bexecutive\b", r"\bboard\b",
        r"\bcompliance\b", r"\bmandatory\b", r"\brequired by\b", r"\bIT Security\b",
        r"\bHR\b.*\brequire", r"legal(ly)? require", r"official(ly)?", r"authorized",
    ],
    "scarcity": [
        r"only \d+ spots?", r"limited (availability|spots?|slots?|seats?)",
        r"\bexclusive\b", r"few remaining", r"last chance", r"running out",
        r"almost (full|gone|sold out)",
    ],
    "reciprocity": [
        r"\bfree\b", r"\bcomplimentary\b", r"no (obligation|cost|charge|commitment)",
        r"\bgift\b", r"on us\b", r"at no cost", r"for free", r"gratis",
        r"free trial", r"free assessment", r"free (analysis|report|audit)",
    ],
    "personalization": [
        r"\byour (company|team|organization|role|position)\b",
        r"specific(ally)? for you", r"tailored (for|to)", r"custom(ized)? (for|to)",
        r"based on your", r"I noticed (you|your)", r"I've been following",
    ],
    "emotional_pressure": [
        r"you'?re? missing out", r"don'?t let", r"imagine if", r"what if you could",
        r"left behind", r"falling behind", r"can'?t afford to", r"risk (losing|missing)",
        r"your (competitors?|rivals?) (are|have)", r"before it'?s? too late",
    ],
    "impersonation_signals": [
        r"(on behalf of|representing) .{0,30}(CEO|executive|board|director)",
        r"(confidential|strictly confidential)", r"(wire transfer|authorization code)",
        r"(do not (share|forward|reply to anyone else))",
        r"(account (suspended|will be suspended|at risk))",
        r"(verify your (identity|account|credentials))",
        r"(unusual activity|suspicious (login|access))",
    ],
}


class PhishingDetector:
    """Loads the fine-tuned RoBERTa model and scores emails."""

    def __init__(self, model_path=None, threshold=None):
        from transformers import pipeline

        self.threshold = threshold if threshold is not None else config.DEFAULT_THRESHOLD

        if torch.cuda.is_available():
            self.device = 0
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = -1  # CPU

        model_dir = Path(model_path) if model_path else config.MODEL_DIR

        if model_dir.exists() and (model_dir / "config.json").exists():
            model_name = str(model_dir)
            self._model_source = "local"
        else:
            model_name = FALLBACK_MODEL
            self._model_source = "huggingface"

        self._pipe = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            device=self.device,
            truncation=True,
            max_length=config.MAX_LENGTH,
        )

        # Detect which label index is "phishing" vs "legitimate"
        id2label = self._pipe.model.config.id2label
        self._phishing_label = None
        self._legit_label = None
        for idx, lbl in id2label.items():
            lbl_upper = lbl.upper()
            if "PHISH" in lbl_upper or lbl_upper in ("LABEL_1", "1"):
                self._phishing_label = lbl
            elif "LEGIT" in lbl_upper or "SAFE" in lbl_upper or lbl_upper in ("LABEL_0", "0"):
                self._legit_label = lbl

        # Fallback: treat LABEL_1 as phishing, LABEL_0 as legit
        if self._phishing_label is None:
            self._phishing_label = id2label.get(1, "LABEL_1")
        if self._legit_label is None:
            self._legit_label = id2label.get(0, "LABEL_0")

    def scan(self, email_text: str) -> dict:
        if not email_text or not email_text.strip():
            return {
                "verdict": "LEGITIMATE",
                "confidence": 50.0,
                "threshold": self.threshold * 100,
                "risk_level": "LOW",
                "details": {"phishing_score": 0.5, "legitimate_score": 0.5},
                "traits": self.analyze_traits(""),
            }

        # top_k=None returns all labels; return_all_scores was removed in transformers v5
        raw = self._pipe(email_text, top_k=None)
        # raw is either [[{label, score}, ...]] or [{label, score}, ...]
        if raw and isinstance(raw[0], list):
            score_list = raw[0]
        else:
            score_list = raw
        scores = {r["label"]: r["score"] for r in score_list}

        phishing_score = scores.get(self._phishing_label, 0.0)
        legit_score = scores.get(self._legit_label, 1.0 - phishing_score)

        is_phishing = phishing_score >= self.threshold

        if is_phishing:
            verdict = "PHISHING"
            confidence = phishing_score * 100
            if phishing_score >= 0.85:
                risk_level = "HIGH"
            else:
                risk_level = "MEDIUM"
        else:
            verdict = "LEGITIMATE"
            confidence = legit_score * 100
            risk_level = "LOW"

        traits = self.analyze_traits(email_text)

        return {
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "threshold": self.threshold * 100,
            "risk_level": risk_level,
            "details": {
                "phishing_score": round(phishing_score, 4),
                "legitimate_score": round(legit_score, 4),
            },
            "traits": traits,
        }

    def scan_batch(self, emails: list) -> list:
        from rich.progress import track
        return [self.scan(email) for email in track(emails, description="Scanning emails...")]

    def analyze_traits(self, email_text: str) -> dict:
        text_lower = email_text.lower()
        detected_traits = []
        flags = []

        for trait, patterns in TRAIT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    if trait not in detected_traits:
                        detected_traits.append(trait)
                    flags.append(f"Contains {trait.replace('_', ' ')}: '{match.group()}'")
                    break

        total_traits = len(TRAIT_PATTERNS)
        manipulation_score = round(len(detected_traits) / total_traits, 3)

        return {
            "traits_detected": detected_traits,
            "trait_count": len(detected_traits),
            "manipulation_score": manipulation_score,
            "flags": flags,
        }
