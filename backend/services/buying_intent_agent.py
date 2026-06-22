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


POSITIVE_RULES: list[tuple[str, int, str, re.Pattern[str]]] = [
    (
        "explicit_vendor_search",
        35,
        "procurement",
        re.compile(r"\b(looking for|seeking|need|recommend).{0,70}\b(agency|partner|vendor|consultant|provider|firm)\b", re.I),
    ),
    (
        "implementation_need",
        25,
        "implementation",
        re.compile(r"\b(implementation|deploy|roll out|migration|transformation|automation|workflow).{0,60}\b(partner|support|help|consultant|vendor)\b", re.I),
    ),
    (
        "rfp_or_shortlist",
        30,
        "formal_procurement",
        re.compile(r"\b(rfp|rfq|rfi|request for proposal|vendor evaluation|shortlist|evaluating vendors|procurement)\b", re.I),
    ),
    (
        "urgent_business_pain",
        18,
        "pain",
        re.compile(r"\b(urgent|struggling|blocked|not working|need to fix|need support|scaling|pipeline|attribution|growth stalled)\b", re.I),
    ),
    (
        "first_party_or_engagement",
        12,
        "first_party",
        re.compile(r"\b(pricing page|demo request|product page|docs viewed|email reply|opened email|visited website|trial)\b", re.I),
    ),
    (
        "growth_event",
        10,
        "firmographic_event",
        re.compile(r"\b(raised funding|new market|expansion|new office|launching|hiring spree|new product)\b", re.I),
    ),
]

NEGATIVE_RULES: list[tuple[str, int, re.Pattern[str]]] = [
    ("recruitment_post", 40, re.compile(r"\b(hiring|job opening|open role|send resume|apply now|mandatory skills|years of experience)\b", re.I)),
    ("seller_promotion", 35, re.compile(r"\b(we help|i help|book a call|dm me|available for work|free consultation|hire me)\b", re.I)),
    ("educational_content", 25, re.compile(r"\b(how to|tips for|lessons learned|best practices|the future of|case study)\b", re.I)),
    ("news_or_generic", 12, re.compile(r"\b(announcing|newsletter|podcast|webinar|thoughts on|trend)\b", re.I)),
]


def _stage(score: int) -> tuple[str, str, bool]:
    if score >= 80:
        return "hot", "tier_1", True
    if score >= 60:
        return "active_research", "tier_2", False
    if score >= 35:
        return "problem_aware", "tier_3", False
    return "cold_or_noise", "low", False


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
    elif verification_category in {"RECRUITMENT", "SELLER_PROMOTION", "EDUCATIONAL", "THOUGHT_LEADERSHIP", "NEWS"}:
        score -= 20
        negative_signals.append(f"final_verifier_{verification_category.lower()}")
        trace.append({"rule": f"final_verifier_{verification_category.lower()}", "weight": -20, "matched": True})

    score = max(0, min(100, score))
    stage, priority, approval_required = _stage(score)
    signal_type = signal_types[0] if signal_types else "unclear"
    play, action = _recommended_play(stage, signal_type)

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
    )


def buying_intent_as_dict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return asdict(analyze_buying_intent(*args, **kwargs))
