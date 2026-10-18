from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class VerificationResult:
    category: str
    confidence: float
    rationale: str
    should_export: bool
    explanation_reason: str = ""  # Human-friendly explanation for rejections


# Rejection reason explanations
REJECTION_REASONS = {
    "RECRUITMENT": "This appears to be a job posting or recruitment effort, not a buyer looking for external services.",
    "SELLER_PROMOTION": "This appears to be vendor/service provider self-promotion, not a buyer seeking external help.",
    "EDUCATIONAL": "This appears to be educational content or thought leadership, not an active procurement signal.",
    "THOUGHT_LEADERSHIP": "This appears to be industry commentary or insights, not an active buyer signal.",
    "NEWS": "This appears to be news or announcement, not an active buyer seeking external services.",
    "CANDIDATE_SELF_PROMOTION": "This appears to be a candidate seeking employment, not a buyer organization.",
    "UNKNOWN": "This doesn't match clear procurement intent patterns.",
}

# Acceptance reason explanations
ACCEPTANCE_REASONS = {
    "PROCUREMENT_BUYER": "Active buyer seeking external services, vendors, agencies, or implementation partners.",
    "HIRING_COMPANY": "Company actively hiring and seeking recruitment or staffing services.",
    "RECRUITMENT_BUYER": "Buyer seeking recruitment agencies, staffing partners, or talent acquisition services.",
    "JOB_OPPORTUNITY": "Job opportunity for candidates seeking employment.",
    "FRACTIONAL_OPPORTUNITY": "Seeking fractional executive or consulting services (CMO, CTO, CFO, etc.).",
}


_BUYER = re.compile(
    r"\b(looking for|need|needs|seeking|recommend|recommendations for|searching for).{0,60}\b(agency|partner|vendor|consultant|service provider|solution provider|implementation partner|managed service)\b",
    re.IGNORECASE,
)
# Job posts are identified by hiring language, not by the presence of a job title.
# (The previous pattern rejected any buyer who mentioned "our marketing manager".)
_JOB = re.compile(
    r"\b(we are hiring|we're hiring|hiring now|now hiring|job opening|send resume|apply now|apply here|open role|open position|mandatory skills|years of experience|#hiring|this position is based)\b",
    re.IGNORECASE,
)
_SELLER = re.compile(
    r"\b(i help|we help|available for work|open for projects|book a call|free consultation|dm for details|hire me|work with me)\b",
    re.IGNORECASE,
)
_EDU = re.compile(
    r"\b(tips for|lessons learned|how to|the future of|best practices|thought leadership|case study|what i learned|"
    r"why companies need|why (does|do) your|your business need|most (businesses|companies|small businesses)|"
    r"here are (a few|the|some)|things to check|ultimate guide|top \d+|\d+ (tips|ways|reasons)|i've (worked|helped)|i helped)\b",
    re.IGNORECASE,
)
_RECRUITMENT_BUYER = re.compile(
    r"\b(need|needs|looking for|seeking|recommend|recommendations for|shortlist).{0,70}\b(recruiter|recruitment agency|recruiting agency|"
    r"staffing partner|staffing agency|staffing firm|rpo|talent acquisition partner|hiring support|executive search|search firm|headhunter|head hunter)\b",
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

# A buyer speaks in the first person about a need. Content ABOUT buyers ("why does
# your business need", "most businesses go looking for") does not. This is the
# single distinction the original verifier lacked.
_FIRST_PERSON_NEED = re.compile(
    r"\b(we|we're|we are|our (company|team|startup|business|org|marketing manager)|i)\b.{0,60}\b(need|needs|looking for|seeking|in the market for)\b",
    re.IGNORECASE,
)
_SECOND_PERSON_OR_GENERIC = re.compile(
    r"\b(your (business|company|team|brand)|most (businesses|companies|founders|teams)|businesses (that|who)|companies (that|who)|"
    r"those are (useful )?signals|the irony)\b",
    re.IGNORECASE,
)


def verify_post(text: str, lead_objective: str = "agency_procurement") -> VerificationResult:
    t = (text or "").strip()
    lower = t.lower()
    objective = (lead_objective or "agency_procurement").lower()
    first_person_need = bool(_FIRST_PERSON_NEED.search(lower))

    # Seller self-promotion overrides everything: a vendor describing what they
    # offer is never a buyer, however buyer-like the surrounding words are.
    if _SELLER.search(lower):
        return VerificationResult("SELLER_PROMOTION", 0.94, "seller_pitch_detected", False, REJECTION_REASONS.get("SELLER_PROMOTION", ""))
    # Educational / generic-subject content is rejected unless the author states
    # a first-person need for a provider ("not sure how to do this - we need a consultant").
    if (_EDU.search(lower) or _SECOND_PERSON_OR_GENERIC.search(lower)) and not (first_person_need and _BUYER.search(lower)):
        return VerificationResult("EDUCATIONAL", 0.90, "educational_or_thought_leadership", False, REJECTION_REASONS.get("EDUCATIONAL", ""))
    if _JOB.search(lower):
        if objective == "candidate_job_search":
            if _CANDIDATE_SELF_PROMO.search(lower):
                return VerificationResult("CANDIDATE_SELF_PROMOTION", 0.92, "candidate_self_promotion_not_job_opening", False, REJECTION_REASONS.get("CANDIDATE_SELF_PROMOTION", ""))
            return VerificationResult("JOB_OPPORTUNITY", 0.91, "job_opportunity_detected_for_candidate_search", True, ACCEPTANCE_REASONS.get("JOB_OPPORTUNITY", ""))
        if objective == "recruitment_clients":
            if _CANDIDATE_SELF_PROMO.search(lower):
                return VerificationResult("CANDIDATE_SELF_PROMOTION", 0.92, "candidate_self_promotion_not_hiring_company", False, REJECTION_REASONS.get("CANDIDATE_SELF_PROMOTION", ""))
            return VerificationResult("HIRING_COMPANY", 0.88, "hiring_demand_detected_for_recruitment_client_mining", True, ACCEPTANCE_REASONS.get("HIRING_COMPANY", ""))
        return VerificationResult("RECRUITMENT", 0.96, "job_posting_detected", False, REJECTION_REASONS.get("RECRUITMENT", ""))
    if objective == "recruitment_clients" and _RECRUITMENT_BUYER.search(lower):
        return VerificationResult("RECRUITMENT_BUYER", 0.91, "external_recruitment_or_staffing_need_detected", True, ACCEPTANCE_REASONS.get("RECRUITMENT_BUYER", ""))
    if objective == "fractional_executive" and _FRACTIONAL.search(lower):
        return VerificationResult("FRACTIONAL_OPPORTUNITY", 0.90, "fractional_or_executive_consulting_need_detected", True, ACCEPTANCE_REASONS.get("FRACTIONAL_OPPORTUNITY", ""))
    if _BUYER.search(lower):
        return VerificationResult("PROCUREMENT_BUYER", 0.88, "buyer_procurement_intent_detected", True, ACCEPTANCE_REASONS.get("PROCUREMENT_BUYER", ""))
    return VerificationResult("NEWS", 0.42, "unclear_intent", False, REJECTION_REASONS.get("UNKNOWN", ""))
