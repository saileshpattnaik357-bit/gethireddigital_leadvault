from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any


def _domain(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url if "://" in url else "https://" + url)
    host = parsed.netloc.lower().removeprefix("www.")
    return host


def _infer_region(text: str) -> str:
    body = text.lower()
    if re.search(r"\b(india|bangalore|bengaluru|mumbai|delhi|hyderabad|pune)\b", body):
        return "India"
    if re.search(r"\b(uk|london|united kingdom|england)\b", body):
        return "United Kingdom"
    if re.search(r"\b(us|usa|united states|new york|san francisco|austin|california)\b", body):
        return "United States"
    if re.search(r"\b(canada|toronto|vancouver)\b", body):
        return "Canada"
    return ""


def _infer_industry(text: str) -> str:
    body = text.lower()
    mapping = {
        "Healthcare": r"\b(healthcare|clinic|hospital|patient|medical|clinical)\b",
        "B2B SaaS": r"\b(saas|software|platform|subscription|b2b)\b",
        "Recruitment": r"\b(recruit|staffing|talent|hiring|hr)\b",
        "Marketing": r"\b(marketing|seo|ppc|brand|content|growth)\b",
        "AI / Automation": r"\b(ai|automation|workflow|agent|llm)\b",
    }
    for label, pattern in mapping.items():
        if re.search(pattern, body):
            return label
    return ""


def enrich_leads(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        text = " ".join(str(item.get(key, "")) for key in ["Client Intent Signal", "Company Name", "Company Website", "Client Query Post URL", "Service Category"])
        domain = _domain(str(item.get("Company Website") or item.get("Client Query Post URL") or ""))
        if domain and not item.get("Company Website"):
            item["Company Website"] = f"https://{domain}"
        if not item.get("Industry"):
            item["Industry"] = _infer_industry(text)
        if not item.get("Region"):
            item["Region"] = _infer_region(text)
        if not item.get("Estimated Deal Value") or item.get("Estimated Deal Value") == "TBD":
            item["Estimated Deal Value"] = _estimate_deal_value(str(item.get("Service Category") or ""), text)
        notes = str(item.get("Notes") or "")
        stamp = datetime.now(timezone.utc).isoformat()
        item["Notes"] = f"{notes} | local_enriched_at={stamp}".strip(" |")
        enriched.append(item)
    return enriched


def _estimate_deal_value(service_category: str, text: str) -> str:
    body = f"{service_category} {text}".lower()
    if any(term in body for term in ["enterprise", "transformation", "implementation", "revops", "ai"]):
        return "$8,000-$25,000"
    if any(term in body for term in ["seo", "content", "marketing", "paid"]):
        return "$3,000-$12,000"
    if any(term in body for term in ["job", "hiring", "recruitment", "staffing"]):
        return "$2,000-$15,000"
    return "$2,500-$10,000"

