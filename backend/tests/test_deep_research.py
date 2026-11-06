from backend.services.deep_research import DeepResearchEngine


def test_deep_research_detection():
    engine = DeepResearchEngine()
    docs = [
        {
            "text": "Acme Corp recently raised Series B funding of $35M to expand its enterprise footprint.",
            "source": "TechCrunch",
            "url": "https://techcrunch.com/acme-series-b",
            "timestamp_utc": "2026-11-05T12:00:00Z",
        },
        {
            "text": "Acme welcomes Sarah Miller as new VP Procurement to spearhead external vendor partnerships.",
            "source": "LinkedIn",
            "url": "https://linkedin.com/posts/sarah-miller-acme",
            "timestamp_utc": "2026-11-06T08:00:00Z",
        },
        {
            "text": "We are migrating to Snowflake and rebuilding our analytics pipeline. Seeking implementation partner RFP.",
            "source": "Reddit",
            "url": "https://reddit.com/r/dataengineering/comments/123",
            "timestamp_utc": "2026-11-06T09:00:00Z",
        },
    ]

    dossier = engine.analyze_company_signals("Acme Corp", "acme.com", docs)

    assert dossier.company_name == "Acme Corp"
    assert dossier.domain == "acme.com"
    assert len(dossier.executive_signals) >= 1
    assert any("VP PROCUREMENT" in s.role for s in dossier.executive_signals)
    assert len(dossier.expansion_signals) >= 2
    assert any(s.signal_type == "funding_round" for s in dossier.expansion_signals)
    assert any(s.signal_type == "tech_migration" for s in dossier.expansion_signals)
    assert dossier.dark_intent_detected is True
    assert dossier.expansion_urgency >= 80
    assert len(dossier.cross_verified_sources) == 3
    assert dossier.freshness_score > 0.8
