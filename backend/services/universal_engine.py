from __future__ import annotations

from dataclasses import asdict, dataclass


INDUSTRY_HINTS = {
    "healthcare": ["healthcare", "medical", "clinic", "hospital", "patient", "clinical"],
    "recruitment": ["recruit", "staff", "talent", "hiring", "rpo", "workforce"],
    "saas": ["saas", "software", "platform", "subscription", "b2b"],
    "ai": ["ai", "automation", "machine learning", "llm", "agent", "workflow"],
    "marketing": ["marketing", "brand", "content", "seo", "ppc", "performance"],
    "revops": ["revops", "revenue operations", "pipeline", "attribution", "sales ops"],
    "consulting": ["consulting", "advisory", "strategy", "fractional", "agency"],
    "manufacturing": ["manufacturing", "factory", "industrial", "supply chain", "operations"],
}

SOURCE_HINTS = {
    "linkedin": ["linkedin", "content", "post", "executive", "founder", "vp", "director"],
    "reddit": ["reddit", "community", "forum", "thread"],
    "google": ["google", "search", "rfp", "rfq", "request for proposal", "vendor"],
    "job_boards": ["hiring", "recruit", "job", "career", "open role", "candidate"],
    "communities": ["slack", "discord", "community", "group", "forum"],
    "marketplaces": ["g2", "capterra", "product hunt", "marketplace", "directory"],
}

BUYER_INTENT_LIBRARY = {
    "agency_search": ["looking for agency", "need an agency", "agency recommendation", "seeking agency partner"],
    "consultant_search": ["looking for consultant", "need external consultant", "seeking consultant", "consulting partner needed"],
    "vendor_search": ["vendor evaluation", "vendor shortlist", "looking for vendor", "request for proposal"],
    "implementation": ["implementation partner", "need help deploying", "need support rolling out", "looking for deployment support"],
    "hiring_intent": ["hiring internal team", "need recruiters", "open roles", "team expansion"],
    "funding_growth": ["raised funding", "new office", "new geography", "expansion", "new product launch"],
}

SERVICE_TO_QUERY_HINTS = {
    "recruitment": ["looking for recruitment agency", "hiring staffing partner", "need recruiters", "rpo provider needed", "urgent hiring support"],
    "healthcare": ["healthcare implementation partner", "clinical workflow consulting", "hospital automation vendor", "digital health agency recommendation"],
    "marketing": ["marketing agency recommendation", "need content marketing partner", "seeking seo consultant", "performance marketing vendor evaluation"],
    "revops": ["looking for revops consultant", "need attribution cleanup support", "sales ops partner needed", "pipeline consulting recommendation"],
    "ai": ["looking for ai implementation partner", "need ai consultant", "seeking automation agency", "vendor for ai workflow deployment"],
}


@dataclass
class UniversalProfile:
    client_type: str
    industries: list[str]
    company_sizes: list[str]
    employee_ranges: list[str]
    geographies: list[str]
    decision_makers: list[str]
    influencers: list[str]
    buyers: list[str]
    champions: list[str]


@dataclass
class DiscoveryPlan:
    buyer_intent_clusters: list[str]
    query_themes: list[str]
    source_channels: list[str]
    linkedin_search_phrases: list[str]
    google_search_phrases: list[str]
    reddit_search_phrases: list[str]
    community_search_phrases: list[str]
    crm_targets: list[str]
    outreach_hooks: list[str]


def _normalize_text(values: list[str]) -> str:
    return " ".join(v for v in values if v).lower()


def _match_hints(text: str, mapping: dict[str, list[str]], default: list[str]) -> list[str]:
    matched = []
    for key, hints in mapping.items():
        if any(hint in text for hint in hints):
            matched.append(key)
    return matched or default


def build_universal_profile(company_name: str, website: str, services: list[str], geography: str = "", icp: str = "", positioning: str = "", customer_examples: list[str] | None = None, founder_profile: str = "") -> UniversalProfile:
    text = _normalize_text([company_name, website, icp, positioning, " ".join(services), " ".join(customer_examples or []), founder_profile, geography])
    industries = _match_hints(text, INDUSTRY_HINTS, ["general b2b"])
    if "ai" in industries and "marketing" in industries:
        client_type = "ai_marketing"
    elif "recruitment" in industries:
        client_type = "recruitment"
    elif "healthcare" in industries:
        client_type = "healthcare"
    elif "revops" in industries:
        client_type = "revops"
    elif "consulting" in industries:
        client_type = "consulting"
    elif "saas" in industries:
        client_type = "saas"
    else:
        client_type = industries[0]

    company_sizes = ["startup", "mid-market", "enterprise"]
    employee_ranges = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
    geographies = [g for g in [geography, "US", "India", "UK", "EU", "Global"] if g]
    decision_makers = ["Founder", "CEO", "CMO", "VP Marketing", "VP Sales", "Head of Growth", "RevOps Lead", "Procurement Lead"]
    influencers = ["Operations Lead", "Marketing Manager", "HR Manager", "Finance Manager", "Product Lead"]
    buyers = ["Founder", "CEO", "VP", "Director", "Head of", "Procurement", "Operations"]
    champions = ["Manager", "Lead", "Coordinator", "Specialist", "Analyst"]

    return UniversalProfile(
        client_type=client_type,
        industries=industries,
        company_sizes=company_sizes,
        employee_ranges=employee_ranges,
        geographies=sorted(set(geographies)),
        decision_makers=decision_makers,
        influencers=influencers,
        buyers=buyers,
        champions=champions,
    )


def build_discovery_plan(company_name: str, website: str, services: list[str], geography: str = "", icp: str = "", positioning: str = "", customer_examples: list[str] | None = None, founder_profile: str = "") -> DiscoveryPlan:
    profile = build_universal_profile(company_name, website, services, geography, icp, positioning, customer_examples, founder_profile)
    service_text = _normalize_text([icp, positioning, " ".join(services), " ".join(customer_examples or [])])
    service_clusters = _match_hints(service_text, SERVICE_TO_QUERY_HINTS, ["general procurement"])

    buyer_intent_clusters: list[str] = []
    for cluster in service_clusters:
        buyer_intent_clusters.extend(BUYER_INTENT_LIBRARY.get(cluster, []))

    source_channels = _match_hints(service_text, SOURCE_HINTS, ["linkedin", "google"])
    if profile.client_type == "recruitment":
        source_channels = ["linkedin", "job_boards", "communities", "google"]
    elif profile.client_type == "healthcare":
        source_channels = ["linkedin", "communities", "google", "marketplaces"]
    elif profile.client_type == "saas":
        source_channels = ["linkedin", "reddit", "google", "marketplaces", "communities"]
    elif profile.client_type == "revops":
        source_channels = ["linkedin", "google", "communities", "reddit"]

    linkedin_search_phrases: list[str] = []
    google_search_phrases: list[str] = []
    reddit_search_phrases: list[str] = []
    community_search_phrases: list[str] = []

    for cluster in service_clusters:
        linkedin_search_phrases.extend([f"looking for {cluster}", f"need {cluster}", f"seeking {cluster}"])
        google_search_phrases.extend([f'"{cluster}" rfp', f'"{cluster}" vendor evaluation', f'"{cluster}" agency recommendation'])
        reddit_search_phrases.extend([f'"{cluster}" recommendation', f'"{cluster}" vendor'])
        community_search_phrases.extend([f'"{cluster}" discussion', f'"{cluster}" support'])

    if profile.client_type in SERVICE_TO_QUERY_HINTS:
        hints = SERVICE_TO_QUERY_HINTS[profile.client_type]
        buyer_intent_clusters.extend(hints)
        linkedin_search_phrases.extend(hints)
        google_search_phrases.extend(hints)

    crm_targets = ["hubspot", "salesforce", "pipedrive"]
    if profile.client_type in {"healthcare", "recruitment"}:
        crm_targets = ["hubspot", "salesforce"]
    if profile.client_type == "saas":
        crm_targets = ["hubspot", "salesforce", "pipedrive"]
    outreach_hooks = [
        f"noticed your team is actively exploring {profile.client_type.replace('_', ' ')} partnerships",
        f"we can help source external support for {', '.join(profile.industries[:2])}",
    ]

    return DiscoveryPlan(
        buyer_intent_clusters=sorted(set(buyer_intent_clusters)),
        query_themes=sorted(set(service_clusters)),
        source_channels=sorted(set(source_channels)),
        linkedin_search_phrases=sorted(set(linkedin_search_phrases)),
        google_search_phrases=sorted(set(google_search_phrases)),
        reddit_search_phrases=sorted(set(reddit_search_phrases)),
        community_search_phrases=sorted(set(community_search_phrases)),
        crm_targets=sorted(set(crm_targets)),
        outreach_hooks=sorted(set(outreach_hooks)),
    )


def profile_as_dict(**kwargs) -> dict:
    return asdict(build_universal_profile(**kwargs))


def plan_as_dict(**kwargs) -> dict:
    return asdict(build_discovery_plan(**kwargs))
