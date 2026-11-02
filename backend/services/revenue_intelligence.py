"""
LeadVault AI: Revenue Intelligence & Deal Valuation Engine (V9 / 29-Field Schema)

Implements:
1. Lead Tier classification ('A' | 'B' | 'C') conforming to LeadVault AGENTS.md TypeScript standard.
2. Estimated Deal Value quantification ($15K–$50K Tactical, $50K–$150K Strategic, $150K–$250K+ Enterprise).
3. Budget Authority derivation (Budget Holder, Influencer, Technical User).
4. Procurement Timeline derivation ('immediate', '1-3mo', 'nurture').
5. Pain point extraction and tailored outreach copy hook.
6. Complete 29 Revenue Intelligence Fields assembly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


@dataclass
class RevenueIntelligenceResult:
    lead_tier: str                      # 'A' | 'B' | 'C'
    estimated_deal_value: str          # "$15K–$50K Tactical" | "$50K–$150K Strategic" | "$150K–$250K+ Enterprise"
    deal_value_min: int                # numeric USD
    deal_value_max: int                # numeric USD
    budget_authority: bool             # True for Tier A budget holders
    authority_role: str                # 'Budget Holder' | 'Influencer' | 'Technical User'
    timeline: str                      # 'immediate' | '1-3mo' | 'nurture'
    urgency_score: int                 # 0 - 100
    pain_point_summary: str            # Extracted need summary
    recommended_outreach_angle: str    # Tailored sales hook
    revenue_intelligence_fields: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Decision Maker Authority Regex Patterns
BUDGET_HOLDER_TITLES = re.compile(
    r"\b(ceo|founder|co-founder|owner|president|cmo|cro|cto|cfo|coo|chief|partner|managing director|vp|vice president|head of growth|head of marketing|head of sales)\b",
    re.I,
)
INFLUENCER_TITLES = re.compile(
    r"\b(director|lead|manager|principal|strategist|growth lead|marketing manager|product manager|team lead)\b",
    re.I,
)
BUDGET_EXPLICIT_SIGNALS = re.compile(
    r"\b(budget allocated|budget set aside|have budget|approved budget|ready to spend|paying vendor|hiring an agency|rfp|procurement budget)\b",
    re.I,
)

# Timeline Patterns
IMMEDIATE_PATTERNS = re.compile(
    r"\b(asap|urgent|immediately|right away|next week|this month|critical|start date|deadline soon|by friday|q[1-4] start|ready to start)\b",
    re.I,
)
SHORT_TERM_PATTERNS = re.compile(
    r"\b(next month|in 30 days|within 60 days|1-2 months|1-3 months|q[1-4]|planning for|next quarter|shortlist)\b",
    re.I,
)

# Deal Size Indicators
ENTERPRISE_SCOPE = re.compile(
    r"\b(enterprise|global|transformation|multi-year|re-platform|full rebuild|migration|managed services|complete overhaul|series b|series c|fortune 500|rfp|rfq)\b",
    re.I,
)
STRATEGIC_SCOPE = re.compile(
    r"\b(fractional|dedicated team|ongoing partner|agency partner|monthly retainer|scale|growth strategy|hubspot implementation|shopify plus|custom development|b2b saas)\b",
    re.I,
)


def extract_authority(text: str, title: str = "") -> tuple[bool, str]:
    """Derive whether the contact is a Budget Holder, Influencer, or Technical User."""
    combined = f"{title} {text}".lower()
    
    if BUDGET_HOLDER_TITLES.search(title) or BUDGET_EXPLICIT_SIGNALS.search(text):
        return True, "Budget Holder"
    if INFLUENCER_TITLES.search(title):
        return False, "Influencer"
    if BUDGET_HOLDER_TITLES.search(text):
        return True, "Budget Holder"
    return False, "Technical User"


def extract_timeline(text: str) -> str:
    """Derive the project timeline."""
    if IMMEDIATE_PATTERNS.search(text):
        return "immediate"
    if SHORT_TERM_PATTERNS.search(text):
        return "1-3mo"
    return "nurture"


def estimate_deal_value(text: str, intent_score: int, service_category: str = "") -> tuple[str, int, int]:
    """Estimate commercial deal value based on scope, signals, and intent."""
    if ENTERPRISE_SCOPE.search(text) or "rfp" in text.lower():
        return "$150K–$250K+ Enterprise", 150000, 250000
    if STRATEGIC_SCOPE.search(text) or intent_score >= 75:
        return "$50K–$150K Strategic", 50000, 150000
    return "$15K–$50K Tactical", 150000 // 10, 50000


def extract_pain_point(text: str) -> str:
    """Extract a concise summary of the core need or pain."""
    cleaned = " ".join(text.replace("\n", " ").split())
    # Try finding sentences containing trigger words
    match = re.search(
        r"([^.!?]{10,120}?(?:looking for|need|seeking|recommend|partner with|help with|struggling with)[^.!?]{5,100}?[.!?]?)",
        cleaned,
        re.I,
    )
    if match:
        snippet = match.group(1).strip()
        if len(snippet) > 15:
            return snippet[:160]
    return cleaned[:140] if cleaned else "Active procurement requirement"


def generate_outreach_angle(pain: str, service_category: str, deal_type: str) -> str:
    """Generate a high-converting, tailored 1:1 outreach angle."""
    if "agency" in pain.lower() or "partner" in pain.lower():
        return f"Reference their active search for an external partner and present proven client case studies addressing: '{pain[:80]}'."
    if "implementation" in pain.lower() or "migration" in pain.lower():
        return f"Highlight rapid technical delivery, zero downtime, and specialized architecture for '{pain[:80]}'."
    return f"Directly address stated pain point: '{pain[:80]}' with a personalized audit framework."


def analyze_revenue_intelligence(
    *,
    text: str,
    intent_score: int,
    confidence_score: float = 0.5,
    title: str = "",
    company_name: str = "",
    industry: str = "",
    source: str = "",
    category: str = "PROCUREMENT_BUYER",
    service_category: str = "procurement",
) -> RevenueIntelligenceResult:
    """
    Perform deep revenue intelligence analysis on a qualified lead candidate.
    Maps to the 29 Revenue Intelligence Fields standard.
    """
    is_budget_authority, authority_role = extract_authority(text, title)
    timeline = extract_timeline(text)
    deal_label, deal_min, deal_max = estimate_deal_value(text, intent_score, service_category)
    pain_point = extract_pain_point(text)
    outreach_angle = generate_outreach_angle(pain_point, service_category, deal_label)

    # Urgency score (0 - 100)
    urgency = 50
    if timeline == "immediate":
        urgency += 35
    elif timeline == "1-3mo":
        urgency += 15
    if is_budget_authority:
        urgency += 15
    urgency = min(100, urgency)

    # Lead Tier classification conforming to AGENTS.md TypeScript standard
    if intent_score >= 70 and confidence_score >= 0.70 and is_budget_authority and timeline in {"immediate", "1-3mo"}:
        lead_tier = "A"
    elif intent_score >= 45 and category not in {"RECRUITMENT", "SELLER_PROMOTION"}:
        lead_tier = "B"
    else:
        lead_tier = "C"

    # Assemble the 29 Revenue Intelligence Fields
    rev_fields = {
        # Contact Intelligence (1-8)
        "Contact_Name": title or "Executive Prospect",
        "Title": title or authority_role,
        "Seniority_Level": authority_role,
        "Budget_Authority": is_budget_authority,
        "Decision_Role": authority_role,
        "Contact_Channel": source or "LinkedIn Public Post",
        "Contact_Verified": bool(title),
        "Location_Scope": "Global / Remote",
        # Sales Intelligence (9-18)
        "Company_Name": company_name or "Prospect Enterprise",
        "Industry_Vertical": industry or "B2B / Technology Services",
        "Company_Headcount_Band": "50–250 employees (Estimated)",
        "Revenue_Band": "$5M–$50M ARR (Estimated)",
        "Lead_Tier": lead_tier,
        "Intent_Score": intent_score,
        "Intent_Confidence": round(confidence_score, 2),
        "Buying_Stage": "hot" if lead_tier == "A" else ("active_research" if lead_tier == "B" else "noise"),
        "Buying_Signal_Type": service_category,
        "Pain_Point_Summary": pain_point,
        # Revenue Intelligence (19-29)
        "Estimated_Deal_Value": deal_label,
        "Deal_Value_Min_USD": deal_min,
        "Deal_Value_Max_USD": deal_max,
        "Purchasing_Timeline": timeline,
        "Urgency_Index": urgency,
        "Outreach_Play": "High-Intent Founder Outreach" if lead_tier == "A" else "SDR Procurement Sequence",
        "Recommended_Angle": outreach_angle,
        "Procurement_Type": "External Vendor Search" if is_budget_authority else "Team Requirement Exploration",
        "Verification_Status": "Dual-Proof Verified" if category == "PROCUREMENT_BUYER" else category,
        "Compliance_Audit_Tag": "Public Signal / Legitimate Interest (GDPR Art 6)",
        "Next_Best_Action": f"Initiate 1:1 outreach via {source} addressing: {pain_point[:60]}",
    }

    return RevenueIntelligenceResult(
        lead_tier=lead_tier,
        estimated_deal_value=deal_label,
        deal_value_min=deal_min,
        deal_value_max=deal_max,
        budget_authority=is_budget_authority,
        authority_role=authority_role,
        timeline=timeline,
        urgency_score=urgency,
        pain_point_summary=pain_point,
        recommended_outreach_angle=outreach_angle,
        revenue_intelligence_fields=rev_fields,
    )
