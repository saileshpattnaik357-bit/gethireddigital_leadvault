from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class VerificationResult:
    category: str
    confidence: float
    rationale: str
    should_export: bool


_BUYER = re.compile(
    r"\b(looking for|need|seeking|recommend|searching for).{0,60}\b(agency|partner|vendor|consultant|service provider|solution provider|implementation partner|managed service)\b",
    re.IGNORECASE,
)
_JOB = re.compile(
    r"\b(we are hiring|we're hiring|hiring now|job opening|send resume|apply now|open role|mandatory skills|years of experience|engineer|developer|analyst|manager)\b",
    re.IGNORECASE,
)
_SELLER = re.compile(
    r"\b(i help|we help|available for work|open for projects|book a call|free consultation|dm for details|hire me|work with me)\b",
    re.IGNORECASE,
)
_EDU = re.compile(
    r"\b(tips for|lessons learned|how to|the future of|best practices|thought leadership|case study|what i learned|why companies need)\b",
    re.IGNORECASE,
)


def verify_post(text: str) -> VerificationResult:
    t = (text or "").strip()
    lower = t.lower()

    if _JOB.search(lower):
        return VerificationResult("RECRUITMENT", 0.96, "job_posting_detected", False)
    if _SELLER.search(lower):
        return VerificationResult("SELLER_PROMOTION", 0.94, "seller_pitch_detected", False)
    if _EDU.search(lower):
        return VerificationResult("EDUCATIONAL", 0.90, "educational_or_thought_leadership", False)
    if _BUYER.search(lower):
        return VerificationResult("PROCUREMENT_BUYER", 0.88, "buyer_procurement_intent_detected", True)
    return VerificationResult("NEWS", 0.42, "unclear_intent", False)

