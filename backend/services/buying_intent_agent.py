from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Any


@dataclass
class BuyingIntentResult:
    intent_score: int
    buying_stage: str
    priority: str
    signal_type: str
    evidence: list[str]
    negative_signals: list[str]
    recommended_play: str
    next_action: str
    approval_required: bool
    explainability_trace: list[dict[str, Any]]
    scored_at_utc: str
    confidence_score: float = 0.5  # 0.0 to 1.0, confidence in the classification


POSITIVE_RULES: list[tuple[str, int, str, re.Pattern[str]]] = [
    (
        "explicit_vendor_search",
        35,
        "procurement",
        re.compile(r"\b(looking for|seeking|need|recommend|searching for).{0,70}\b(agency|partner|vendor|consultant|provider|firm|implementation partner|service provider|external support|outsourced team)\b", re.I),
    ),
    (
        "partner_search_variants",
        32,
        "procurement",
        re.compile(r"\b(partner with|partnering with|looking to hire|hire an|hire external|engage|engagement with|work with|collaborate with).{0,60}\b(agency|consultant|vendor|partner|firm|expert)\b", re.I),
    ),
    (
        "implementation_need",
        25,
        "implementation",
        re.compile(r"\b(implementation|deploy|roll out|migration|transformation|automation|workflow).{0,60}\b(partner|support|help|consultant|vendor|agency)\b", re.I),
    ),
    (
        "fractional_or_outsource",
        28,
        "procurement",
        re.compile(r"\b(fractional|outsourc|external team|third party|white label|wholesale|managed services|resell|reseller|agency for)\b", re.I),
    ),
    (
        "service_provider_request",
        30,
        "procurement",
        re.compile(r"\b(looking for a|need a|seeking a|evaluating|shortlisting|requirements|considering|exploring).{0,40}\b(agency|consultant|partner|vendor|solution|provider|specialist)\b", re.I),
    ),
    (
        "rfp_or_shortlist",
        30,
        "formal_procurement",
        re.compile(r"\b(rfp|rfq|rfi|request for proposal|vendor evaluation|shortlist|evaluating vendors|procurement|call for|bid for|request for)\b", re.I),
    ),
    (
        "recommendation_request",
        27,
        "procurement",
        re.compile(r"\b(recommend|recommendation|suggestion|referral|who do you|anyone know|anyone used|best in).{0,50}\b(agency|consultant|vendor|partner|solution|company|firm)\b", re.I),
    ),
    (
        "budget_allocation",
        20,
        "procurement",
        re.compile(r"\b(budget|allocat|invest in|spend on|planning|budget for|funding for|earmark|set aside).{0,50}\b(external|agency|consultant|vendor|partner|support)\b", re.I),
    ),
    (
        "hiring_external",
        25,
        "procurement",
        re.compile(r"\b(hiring external|hiring outside|bringing in|onboarding|contractor|freelancer|specialist|expert|dedicated team)\b", re.I),
    ),
    (
        "urgent_business_pain",
        18,
        "pain",
        re.compile(r"\b(urgent|struggling|blocked|not working|need to fix|need support|scaling|pipeline|attribution|growth stalled|help with|support for|need better)\b", re.I),
    ),
    (
        "specific_service_need",
        24,
        "procurement",
        re.compile(r"\b(need help with|help with|support for|looking for.*support|need.*implementation|seeking.*solution|require.*expertise).{0,40}\b(seo|marketing|sales|dev|revenue|growth|automation|crm|implementation)\b", re.I),
    ),
    (
        "decision_maker_signal",
        16,
        "procurement",
        re.compile(r"\b(ceo|cmo|vp|founder|founder here|running|building|leading).{0,40}\b(looking for|need|seeking|partner)\b", re.I),
    ),
    (
        "first_party_or_engagement",
        12,
        "first_party",
        re.compile(r"\b(pricing page|demo request|product page|docs viewed|email reply|opened email|visited website|trial|sign up|register|contact)\b", re.I),
    ),
    (
        "growth_event",
        10,
        "firmographic_event",
        re.compile(r"\b(raised funding|new market|expansion|new office|launching|hiring spree|new product|growing|scaling up)\b", re.I),
    ),
]

NEGATIVE_RULES: list[tuple[str, int, re.Pattern[str]]] = [
    ("recruitment_post", 40, re.compile(r"\b(hiring|job opening|open role|send resume|apply now|mandatory skills|years of experience|career opportunity|now hiring|join our team|expand our team|contractor needed|freelancer needed|gig work|temp position)\b", re.I)),
    ("seller_promotion", 35, re.compile(r"\b(we help|i help|book a call|dm me|available for work|free consultation|hire me|our services|our expertise|reach out to|contact us|let me know|offering services|providing services|specializes in|expert in|open for|available now|ready to start)\b", re.I)),
    ("educational_content", 25, re.compile(r"\b(how to|tips for|lessons learned|best practices|the future of|case study|guide to|tutorial|learn how|strategies for|5 ways|7 steps|10 tips|framework for)\b", re.I)),
    ("vendor_self_promotion", 30, re.compile(r"\b(our product|our platform|our solution|we solve|we provide|we deliver|we specialize|built to|designed to|helps you|enables you|allowing companies|allowing you).{0,40}\b(solve|manage|improve|scale|automate|streamline)\b", re.I)),
    ("thought_leadership", 20, re.compile(r"\b(thread|thoughts on|my take|perspective|opinion on|observations|insights on|in my experience|imo|imho|just my thoughts)\b", re.I)),
    ("news_or_generic", 12, re.compile(r"\b(announcing|newsletter|podcast|webinar|thoughts on|trend|breaking|news|report|study|research|analysis|roundup)\b", re.I)),
    ("job_description", 38, re.compile(r"\b(job description|position available|open position|role available|job req|req opened|headcount|ats|applicant tracking|full-time|part-time|remote|onsite).{0,30}\b(hiring|open|role|position|available)\b", re.I)),
]


def _stage(score: int) -> tuple[str, str, bool]:
    if score >= 80:
        return "hot", "tier_1", True
    if score >= 60:
        return "active_research", "tier_2", False
    if score >= 35:
        return "problem_aware", "tier_3", False
    return "cold_or_noise", "low", False


def _calculate_confidence(evidence: list[str], negative_signals: list[str], score: int, text_length: int) -> float:
    """Calculate confidence in the classification (0.0 to 1.0)."""
    confidence = 0.5

    # More positive signals = higher confidence
    signal_count_boost = min(len(evidence) * 0.1, 0.3)
    confidence += signal_count_boost

    # Fewer negative signals = higher confidence
    if negative_signals:
        signal_conflict_penalty = min(len(negative_signals) * 0.08, 0.25)
        confidence -= signal_conflict_penalty

    # Strong scores (hot/active_research) = higher confidence
    if score >= 80:
        confidence += 0.15
    elif score >= 60:
        confidence += 0.10
    elif score < 35:
        confidence -= 0.10

    # Longer text generally means more context = higher confidence
    if text_length > 200:
        confidence += 0.10
    elif text_length < 50:
        confidence -= 0.05

    # Clamp to 0.0-1.0 range
    return max(0.0, min(1.0, confidence))


def _recommended_play(stage: str, signal_type: str) -> tuple[str, str]:
    if stage == "hot":
        return "high_intent_founder_led_outreach", "research account, enrich decision makers, draft 1:1 outreach, request approval"
    if stage == "active_research":
        return "sdr_led_procurement_sequence", "enrich account, generate contextual email and LinkedIn sequence"
    if signal_type in {"pain", "first_party", "firmographic_event"}:
        return "nurture_with_research", "save signal, watch for procurement language, send light educational touch"
    return "monitor_only", "keep in account graph and wait for stronger signal"


def analyze_buying_intent(
    text: str,
    account: dict[str, Any] | None = None,
    verification_category: str | None = None,
) -> BuyingIntentResult:
    body = " ".join(
        [
            text or "",
            str((account or {}).get("company", "")),
            str((account or {}).get("website", "")),
            str((account or {}).get("industry", "")),
            str((account or {}).get("source", "")),
        ]
    )

    score = 10
    evidence: list[str] = []
    negative_signals: list[str] = []
    trace: list[dict[str, Any]] = []
    signal_types: list[str] = []

    for rule, weight, signal_type, pattern in POSITIVE_RULES:
        if pattern.search(body):
            score += weight
            signal_types.append(signal_type)
            evidence.append(rule)
            trace.append({"rule": rule, "weight": weight, "matched": True, "signal_type": signal_type})

    for rule, penalty, pattern in NEGATIVE_RULES:
        if pattern.search(body):
            score -= penalty
            negative_signals.append(rule)
            trace.append({"rule": rule, "weight": -penalty, "matched": True})

    if verification_category == "PROCUREMENT_BUYER":
        score += 20
        evidence.append("final_verifier_procurement_buyer")
        trace.append({"rule": "final_verifier_procurement_buyer", "weight": 20, "matched": True})
    elif verification_category in {"HIRING_COMPANY", "RECRUITMENT_BUYER", "JOB_OPPORTUNITY", "FRACTIONAL_OPPORTUNITY"}:
        score += 95
        evidence.append(f"final_verifier_{verification_category.lower()}")
        trace.append({"rule": f"final_verifier_{verification_category.lower()}", "weight": 95, "matched": True})
    elif verification_category in {"RECRUITMENT", "SELLER_PROMOTION", "EDUCATIONAL", "THOUGHT_LEADERSHIP", "NEWS"}:
        score -= 20
        negative_signals.append(f"final_verifier_{verification_category.lower()}")
        trace.append({"rule": f"final_verifier_{verification_category.lower()}", "weight": -20, "matched": True})

    score = max(0, min(100, score))
    stage, priority, approval_required = _stage(score)
    category_signal_types = {
        "HIRING_COMPANY": "recruitment_client_hiring_demand",
        "RECRUITMENT_BUYER": "recruitment_procurement",
        "JOB_OPPORTUNITY": "candidate_job_opportunity",
        "FRACTIONAL_OPPORTUNITY": "fractional_executive_opportunity",
    }
    signal_type = category_signal_types.get(verification_category or "", signal_types[0] if signal_types else "unclear")
    play, action = _recommended_play(stage, signal_type)

    confidence = _calculate_confidence(evidence, negative_signals, score, len(body))

    return BuyingIntentResult(
        intent_score=score,
        buying_stage=stage,
        priority=priority,
        signal_type=signal_type,
        evidence=evidence,
        negative_signals=negative_signals,
        recommended_play=play,
        next_action=action,
        approval_required=approval_required,
        explainability_trace=trace,
        scored_at_utc=datetime.now(timezone.utc).isoformat(),
        confidence_score=confidence,
    )


def buying_intent_as_dict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return asdict(analyze_buying_intent(*args, **kwargs))
