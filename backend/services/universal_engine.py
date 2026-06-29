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

OBJECTIVE_ALIASES = {
    "agency_procurement": [
        "agency",
        "agency buyer",
        "procurement",
        "vendor",
        "client leads",
        "buying intent",
        "digital leads",
        "gethired digital",
    ],
    "recruitment_clients": [
        "recruitment",
        "staffing",
        "hirex",
        "hr leads",
        "hiring clients",
        "companies hiring",
        "rpo",
        "talent acquisition clients",
    ],
    "candidate_job_search": [
        "job seeker",
        "job search",
        "candidate",
        "candidate job mining",
        "jobs for candidates",
        "open roles",
        "career opportunities",
    ],
    "fractional_executive": [
        "fractional cmo",
        "fractional executive",
        "executive consulting",
        "consulting opportunity",
        "advisory opportunity",
        "growth advisor",
    ],
}

OBJECTIVE_CONFIGS = {
    "agency_procurement": {
        "label": "Agency / Vendor Buyer Leads",
        "description": "Find companies actively seeking agencies, consultants, vendors, implementation partners, or outsourced support.",
        "accepted_categories": ["PROCUREMENT_BUYER"],
        "source_channels": ["linkedin", "google", "communities", "marketplaces"],
        "query_templates": [
            "looking for {service} agency",
            "need {service} consultant",
            "seeking {service} partner",
            "{service} agency recommendation",
            "vendor for {service}",
            "request for proposal {service}",
        ],
        "google_templates": [
            'site:linkedin.com/posts "{service} agency recommendation"',
            '"{service}" "request for proposal"',
            '"{service}" "vendor evaluation"',
            '"looking for" "{service}" "agency"',
        ],
        "positive_signals": ["agency search", "consultant search", "vendor evaluation", "RFP/RFQ", "outsourcing", "implementation partner"],
        "negative_filters": ["job post", "employee hiring", "seller promotion", "education", "thought leadership"],
    },
    "recruitment_clients": {
        "label": "Recruitment / Staffing Client Leads",
        "description": "Find companies showing hiring demand that a recruitment, staffing, or RPO firm can serve.",
        "accepted_categories": ["HIRING_COMPANY", "RECRUITMENT_BUYER"],
        "source_channels": ["linkedin", "job_boards", "google", "communities"],
        "query_templates": [
            "we are hiring {service}",
            "hiring {service} team",
            "urgent hiring {service}",
            "need recruiters for {service}",
            "looking for staffing partner {service}",
            "rpo provider needed {service}",
        ],
        "google_templates": [
            '"we are hiring" "{service}"',
            '"urgent hiring" "{service}"',
            '"need recruiters" "{service}"',
            '"staffing partner" "{service}"',
        ],
        "positive_signals": ["active hiring", "urgent roles", "team expansion", "recruiter need", "RPO/staffing partner need"],
        "negative_filters": ["staffing agency promotion", "candidate looking for job", "education", "generic hiring news"],
    },
    "candidate_job_search": {
        "label": "Candidate / Job Opportunity Mining",
        "description": "Find job openings, hiring posts, and career opportunities for a candidate profile.",
        "accepted_categories": ["JOB_OPPORTUNITY"],
        "source_channels": ["linkedin", "job_boards", "google", "communities"],
        "query_templates": [
            "hiring {service}",
            "{service} job opening",
            "{service} open role",
            "{service} remote job",
            "{service} apply now",
            "{service} career opportunity",
        ],
        "google_templates": [
            '"{service}" "job opening"',
            '"{service}" "apply now"',
            '"{service}" "remote"',
            'site:linkedin.com/jobs "{service}"',
        ],
        "positive_signals": ["job opening", "apply now", "open role", "hiring manager post", "career opportunity"],
        "negative_filters": ["agency self-promotion", "course promotion", "candidate resume post", "generic career advice"],
    },
    "fractional_executive": {
        "label": "Fractional Executive / Consulting Opportunities",
        "description": "Find companies seeking fractional CMOs, GTM advisors, RevOps consultants, growth leaders, or executive consultants.",
        "accepted_categories": ["PROCUREMENT_BUYER", "FRACTIONAL_OPPORTUNITY"],
        "source_channels": ["linkedin", "google", "communities", "reddit"],
        "query_templates": [
            "looking for fractional {service}",
            "need interim {service}",
            "seeking {service} consultant",
            "need GTM advisor {service}",
            "looking for growth consultant {service}",
            "fractional CMO recommendation {service}",
        ],
        "google_templates": [
            '"fractional CMO" "looking for"',
            '"GTM advisor" "needed"',
            '"interim marketing leader" "{service}"',
            '"growth consultant" "recommendation"',
        ],
        "positive_signals": ["fractional leader need", "interim executive need", "GTM advisory", "growth consulting", "RevOps support"],
        "negative_filters": ["executive job posting only", "consultant self-promotion", "thought leadership", "course/webinar"],
    },
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
    lead_objective: str
    objective_label: str
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
    lead_objective: str
    objective_label: str
    accepted_categories: list[str]
    positive_signals: list[str]
    negative_filters: list[str]
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


def normalize_objective(lead_objective: str = "", corpus: str = "") -> str:
    requested = (lead_objective or "").strip().lower().replace("-", "_").replace(" ", "_")
    if requested in OBJECTIVE_CONFIGS:
        return requested

    text = f"{lead_objective} {corpus}".lower()
    for objective, aliases in OBJECTIVE_ALIASES.items():
        if any(alias in text for alias in aliases):
            return objective
    return "agency_procurement"


def objective_config(lead_objective: str = "", corpus: str = "") -> dict:
    objective = normalize_objective(lead_objective, corpus)
    return OBJECTIVE_CONFIGS[objective]


def _service_terms(services: list[str], icp: str, positioning: str, customer_examples: list[str] | None = None) -> list[str]:
    terms: list[str] = []
    for value in [*services, icp, positioning, *(customer_examples or [])]:
        for part in str(value or "").replace("/", " ").split("|"):
            cleaned = part.strip(" .,:;").lower()
            if cleaned and len(cleaned) <= 80:
                terms.append(cleaned)
    return list(dict.fromkeys(terms or ["growth", "marketing", "operations", "technology"]))


def build_universal_profile(company_name: str, website: str, services: list[str], geography: str = "", icp: str = "", positioning: str = "", customer_examples: list[str] | None = None, founder_profile: str = "", lead_objective: str = "") -> UniversalProfile:
    text = _normalize_text([company_name, website, icp, positioning, " ".join(services), " ".join(customer_examples or []), founder_profile, geography])
    objective = normalize_objective(lead_objective, text)
    config = OBJECTIVE_CONFIGS[objective]
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

    if objective == "candidate_job_search":
        decision_makers = ["Hiring Manager", "Recruiter", "Talent Acquisition", "Department Head", "Founder"]
        influencers = ["Recruiter", "Sourcer", "HR Coordinator"]
        buyers = ["Candidate target employer", "Hiring team", "Recruiter"]
        champions = ["Recruiter", "Hiring Manager", "Referral contact"]
    elif objective == "recruitment_clients":
        decision_makers = ["Founder", "CEO", "CHRO", "Head of Talent", "HR Director", "Talent Acquisition Lead"]
        influencers = ["HR Manager", "Recruiter", "People Ops", "Department Head"]
        buyers = ["Founder", "Head of Talent", "HR Director", "Hiring Manager"]
        champions = ["Recruiter", "HR Manager", "People Ops"]
    elif objective == "fractional_executive":
        decision_makers = ["Founder", "CEO", "COO", "Board Member", "Investor", "Head of Growth"]
        influencers = ["Marketing Manager", "RevOps Lead", "Sales Leader", "Investor"]
        buyers = ["Founder", "CEO", "Board", "Investor"]
        champions = ["Growth Lead", "Marketing Manager", "RevOps Lead"]

    return UniversalProfile(
        lead_objective=objective,
        objective_label=config["label"],
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


def build_discovery_plan(company_name: str, website: str, services: list[str], geography: str = "", icp: str = "", positioning: str = "", customer_examples: list[str] | None = None, founder_profile: str = "", lead_objective: str = "") -> DiscoveryPlan:
    profile = build_universal_profile(company_name, website, services, geography, icp, positioning, customer_examples, founder_profile, lead_objective)
    config = OBJECTIVE_CONFIGS[profile.lead_objective]
    service_text = _normalize_text([icp, positioning, " ".join(services), " ".join(customer_examples or [])])
    service_clusters = _match_hints(service_text, SERVICE_TO_QUERY_HINTS, ["general procurement"])
    service_terms = _service_terms(services, icp, positioning, customer_examples)

    buyer_intent_clusters: list[str] = []
    for cluster in service_clusters:
        buyer_intent_clusters.extend(BUYER_INTENT_LIBRARY.get(cluster, []))

    source_channels = list(config["source_channels"])
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

    for term in service_terms[:12]:
        linkedin_search_phrases.extend(template.format(service=term) for template in config["query_templates"])
        google_search_phrases.extend(template.format(service=term) for template in config["google_templates"])
        reddit_search_phrases.extend([f'"{term}" recommendation', f'"{term}" help', f'"{term}" hiring'])
        community_search_phrases.extend([f'"{term}" support', f'"{term}" opportunity'])

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
        lead_objective=profile.lead_objective,
        objective_label=config["label"],
        accepted_categories=list(config["accepted_categories"]),
        positive_signals=list(config["positive_signals"]),
        negative_filters=list(config["negative_filters"]),
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
