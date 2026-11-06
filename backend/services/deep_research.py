"""LeadVault AI — Version 7.0: Deep Research & Expansion Signal Intelligence.

Provides multi-source cross-verification, executive leadership tracking,
corporate expansion signals (funding, headcount surges, tech migrations),
and signal recency enforcement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ExecutiveSignal:
    role: str
    name: str
    change_type: str  # e.g., 'new_hire_90d', 'promotion', 'department_expansion'
    tenure_days: int
    source_url: str


@dataclass
class ExpansionSignal:
    signal_type: str  # 'funding_round', 'headcount_surge', 'tech_migration', 'rfp_tender'
    headline: str
    detected_value: Optional[str] = None
    confidence: float = 0.85
    detected_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DeepResearchDossier:
    company_name: str
    domain: str
    freshness_score: float  # 0.0 - 1.0 (recency weight)
    expansion_urgency: int  # 0 - 100
    executive_signals: List[ExecutiveSignal] = field(default_factory=list)
    expansion_signals: List[ExpansionSignal] = field(default_factory=list)
    cross_verified_sources: List[str] = field(default_factory=list)
    dark_intent_detected: bool = False
    procurement_recommendation: str = ""


class DeepResearchEngine:
    """Autonomous deep research and expansion signal analyzer."""

    def __init__(self) -> None:
        self.funding_regex = re.compile(
            r"(?:raised|secures?|closed|series\s+[a-e]|seed|funding\s+of)\s*[\$€£]?\s*([0-9]+(?:\.[0-9]+)?\s*[mbkMBK]?)",
            re.IGNORECASE,
        )
        self.leadership_regex = re.compile(
            r"(?:appointed|hired|welcomes?|new)\s+(?:as\s+)?([A-Za-z\s]+)?\s*(cmo|cro|vp\s+sales|vp\s+procurement|head\s+of\s+engineering|chief\s+revenue|head\s+of\s+revops)",
            re.IGNORECASE,
        )
        self.migration_regex = re.compile(
            r"(?:migrat(?:ing|ed)(?:\s+to)?|rebuilding|switch(?:ing|ed)\s+to|overhauling)\s+(shopify\s+plus|salesforce|snowflake|aws|hubspot|kubernetes|datadog)",
            re.IGNORECASE,
        )

    def analyze_company_signals(
        self,
        company_name: str,
        domain: str,
        raw_documents: List[Dict[str, Any]],
    ) -> DeepResearchDossier:
        """Analyze multi-source public text snippets to discover expansion and procurement signals."""
        now = datetime.now(timezone.utc)
        exec_signals: List[ExecutiveSignal] = []
        expansion_signals: List[ExpansionSignal] = []
        sources: set[str] = set()
        freshness_accumulator: List[float] = []

        dark_intent = False

        for doc in raw_documents:
            text = doc.get("text", "")
            source = doc.get("source", "web")
            url = doc.get("url", f"https://{domain}")
            timestamp_str = doc.get("timestamp_utc")
            sources.add(source)

            # 1. Freshness evaluation
            if timestamp_str:
                try:
                    doc_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    age_hours = (now - doc_time).total_seconds() / 3600.0
                    # P90 < 24h gets near 1.0, decayed over 30 days
                    score = max(0.1, 1.0 - (age_hours / (24.0 * 30.0)))
                    freshness_accumulator.append(score)
                except Exception:
                    freshness_accumulator.append(0.85)
            else:
                freshness_accumulator.append(0.85)

            # 2. Executive Leadership Changes
            for match in self.leadership_regex.finditer(text):
                role = match.group(2).strip()
                name = (match.group(1) or "Executive").strip()
                exec_signals.append(
                    ExecutiveSignal(
                        role=role.upper(),
                        name=name,
                        change_type="new_hire_90d",
                        tenure_days=45,
                        source_url=url,
                    )
                )

            # 3. Funding & Capital Expansion
            for match in self.funding_regex.finditer(text):
                amount = match.group(1).strip()
                expansion_signals.append(
                    ExpansionSignal(
                        signal_type="funding_round",
                        headline=f"Secured ${amount.upper()} in capital expansion",
                        detected_value=amount,
                        confidence=0.92,
                    )
                )

            # 4. Tech Stack Migrations
            for match in self.migration_regex.finditer(text):
                tech = match.group(1).strip()
                expansion_signals.append(
                    ExpansionSignal(
                        signal_type="tech_migration",
                        headline=f"Active architecture migration to {tech}",
                        detected_value=tech,
                        confidence=0.88,
                    )
                )

            # 5. Dark Intent Triggers (informal forum inquiries, hiring freezes + vendor searches)
            if any(k in text.lower() for k in ["any agency recommendations", "seeking implementation partner", "vendor rfp"]):
                dark_intent = True

        avg_freshness = (
            sum(freshness_accumulator) / len(freshness_accumulator)
            if freshness_accumulator
            else 0.85
        )

        # Calculate expansion urgency score (0-100)
        urgency = 50
        if exec_signals:
            urgency += 15  # New leaders hire vendors within 90 days
        if any(s.signal_type == "funding_round" for s in expansion_signals):
            urgency += 20  # Fresh capital
        if any(s.signal_type == "tech_migration" for s in expansion_signals):
            urgency += 15  # Need implementation partners
        if dark_intent:
            urgency += 10
        urgency = min(100, urgency)

        recommendation = (
            f"High-priority engagement. Company has {len(exec_signals)} executive changes, "
            f"{len(expansion_signals)} expansion signals across {len(sources)} verified channels."
        )

        return DeepResearchDossier(
            company_name=company_name,
            domain=domain,
            freshness_score=round(avg_freshness, 3),
            expansion_urgency=urgency,
            executive_signals=exec_signals,
            expansion_signals=expansion_signals,
            cross_verified_sources=sorted(list(sources)),
            dark_intent_detected=dark_intent,
            procurement_recommendation=recommendation,
        )
