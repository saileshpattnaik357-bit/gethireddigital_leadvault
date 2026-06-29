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
_RECRUITMENT_BUYER = re.compile(
    r"\b(need|looking for|seeking|recommend|shortlist).{0,70}\b(recruiter|recruitment agency|staffing partner|rpo|talent acquisition partner|hiring support)\b",
    re.IGNORECASE,
)
_HIRING_COMPANY = re.compile(
    r"\b(we are hiring|we're hiring|hiring now|urgent hiring|open role|job opening|career opportunity|join our team|apply now|send resume|mandatory skills|years of experience)\b",
    re.IGNORECASE,
)
_CANDIDATE_SELF_PROMO = re.compile(
    r"\b(i am looking for|open to work|seeking opportunities|my resume|please refer me|available immediately)\b",
    re.IGNORECASE,
)
_FRACTIONAL = re.compile(
    r"\b(looking for|need|seeking|recommend).{0,80}\b(fractional cmo|interim cmo|gtm advisor|growth advisor|revops consultant|marketing consultant|fractional leader)\b",
    re.IGNORECASE,
)


def verify_post(text: str, lead_objective: str = "agency_procurement") -> VerificationResult:
    t = (text or "").strip()
    lower = t.lower()
    objective = (lead_objective or "agency_procurement").lower()

    if _EDU.search(lower):
        return VerificationResult("EDUCATIONAL", 0.90, "educational_or_thought_leadership", False)
    if _JOB.search(lower):
        if objective == "candidate_job_search":
            if _CANDIDATE_SELF_PROMO.search(lower):
                return VerificationResult("CANDIDATE_SELF_PROMOTION", 0.92, "candidate_self_promotion_not_job_opening", False)
            return VerificationResult("JOB_OPPORTUNITY", 0.91, "job_opportunity_detected_for_candidate_search", True)
        if objective == "recruitment_clients":
            if _CANDIDATE_SELF_PROMO.search(lower):
                return VerificationResult("CANDIDATE_SELF_PROMOTION", 0.92, "candidate_self_promotion_not_hiring_company", False)
            return VerificationResult("HIRING_COMPANY", 0.88, "hiring_demand_detected_for_recruitment_client_mining", True)
        return VerificationResult("RECRUITMENT", 0.96, "job_posting_detected", False)
    if _SELLER.search(lower):
        return VerificationResult("SELLER_PROMOTION", 0.94, "seller_pitch_detected", False)
    if objective == "recruitment_clients" and _RECRUITMENT_BUYER.search(lower):
        return VerificationResult("RECRUITMENT_BUYER", 0.91, "external_recruitment_or_staffing_need_detected", True)
    if objective == "fractional_executive" and _FRACTIONAL.search(lower):
        return VerificationResult("FRACTIONAL_OPPORTUNITY", 0.90, "fractional_or_executive_consulting_need_detected", True)
    if _BUYER.search(lower):
        return VerificationResult("PROCUREMENT_BUYER", 0.88, "buyer_procurement_intent_detected", True)
    return VerificationResult("NEWS", 0.42, "unclear_intent", False)
