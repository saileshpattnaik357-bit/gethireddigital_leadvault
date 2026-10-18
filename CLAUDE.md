# LeadVault CLAUDE.md — Procurement Intelligence Standard

**Inherits from**: Global CLAUDE.md (E:\Claude\CLAUDE.md)  
**Date**: 2026-09-15  
**Project**: LeadVault (Lead Mining Intelligence)  
**Tech Stack**: React (frontend), FastAPI (backend), PostgreSQL, ICP upload

---

## Mission

Build the most precise lead-mining interface — ICP matching, buyer intent signals, export-ready.

---

## Project-Specific Standards

### 1. Lead Intelligence UI/UX (Clarity + Action)
- ✅ **Lead Card**: Company name, contact, ICP match score, intent signals
- ✅ **Filtering**: By lead tier (A/B/C), source, intent strength
- ✅ **Intent Signals**: Budget authority, timeline, active searches
- ✅ **Export**: CSV with all lead data + scoring breakdown

### 2. TypeScript Patterns (LeadVault Priority)

```typescript
type LeadTier = 'A' | 'B' | 'C';

type Lead = 
  | { tier: 'A'; company_name: string; match_score: number; budget_authority: true; timeline: 'immediate' | '1-3mo' }
  | { tier: 'B'; company_name: string; match_score: number; budget_authority: boolean; timeline?: string }
  | { tier: 'C'; company_name: string; match_score: number; budget_authority: false; timeline?: never };
```

### 3. Compliance Checklist (LeadVault)

- [ ] ICP Matching: Accuracy >85%, match reasons shown
- [ ] Data Quality: No duplicate leads, contact validation

---

---

## System Design for LeadVault (Lead Intelligence Infrastructure)

**Primary focus**: NoSQL database (flexible lead attributes vary by source)

### Implementation Priority
1. **NoSQL Database** (flexible lead attributes from LinkedIn, Crunchbase, custom)
2. **Message Queues** (lead classification pipeline)
3. **Rate Limiting** (LinkedIn API quota management)
4. **Idempotency** (prevent duplicate leads from multiple sources)

### Key Patterns
- **Database**: MongoDB (flexible schema for varied lead sources)
- **Caching**: Redis (lead enrichment cache)
- **Message Queue**: RabbitMQ (lead extraction → classification → export)
- **Rate Limiting**: Token bucket (LinkedIn API limits)

**Reference**: SYSTEM_DESIGN_FOR_AGENTS.md (section: LeadVault Procurement)

---

## AI Business Models for LeadVault

**Stage 1: Lead Generation** (LeadVault primary)
- Mine LinkedIn, Crunchbase, web sources
- Filter by ICP criteria
- Score by intent signals
- Export ready-to-contact list

**Stage 3: Lead Reactivation** (LeadVault secondary)
- Identify dormant leads
- Detect company changes (funding, hiring)
- Trigger reactivation campaigns
- Generate new angle emails

**Metrics**:
- ICP accuracy: >85%
- Intent signal hit rate: >60%
- Reactivation rate: >15%

**Reference**: AI_BUSINESS_MODELS.md

---

## Hermes Integration for LeadVault

### Memory System
- **Episodic**: Lead interactions, outreach attempts, conversion outcomes
- **Semantic**: Company attributes, industry data, ICP definitions
- **Procedural**: Lead enrichment workflow, ICP matching patterns

### Autonomous Learning Loop
```
Baseline: ICP accuracy 75%
  ↓ Learn from sales conversion data
Target: 87% accuracy (within 3 months)

Metrics:
  ├─ ICP match accuracy (vs sales closed)
  ├─ Intent signal prediction
  └─ Lead source quality
```

### Scheduled Tasks
- **Daily**: Lead enrichment (background process)
- **Weekly**: ICP accuracy audit + adjustment
- **Monthly**: Sales feedback integration + model update

**Reference**: HERMES_DEEP_DIVE.md

---

## Agent Protocols for LeadVault

**Primary**: WebMCP (access external data sources: LinkedIn, Crunchbase)  
**Secondary**: MCP (internal lead database)

### WebMCP for Data Sources
```
LeadVault Agent → LinkedIn API → Company data
            ↘ Crunchbase API → Funding data
             ↘ Apollo.io → Contact data
```

**Reference**: 6_AGENT_PROTOCOLS_COMPARISON.md

---

## Memory Architecture for LeadVault

### Memory Types
1. **Working Memory**: Current lead being scored
2. **Episodic Memory**: Lead interactions + conversion outcomes
3. **Semantic Memory**: Company attributes, ICP criteria
4. **Procedural Memory**: Lead enrichment workflow

### Storage Backends
- **Vector DB**: Lead similarity (semantic matching)
- **Relational DB**: Structured company + contact data
- **Key-Value**: Lead enrichment cache
- **Graph DB**: Company-person-technology relationships

**Reference**: AI_MEMORY_ARCHITECTURE.md

---

## NLP Patterns for LeadVault

### Named Entity Recognition (NER)
- Extract: Company, Location, Industry, Funding Stage
- From: LinkedIn profiles, Crunchbase entries, web text

### Lemmatization
- Normalize: "companies" → "company", "hiring" → "hire"
- Match job titles across sources

### Embeddings
- Vector similarity: embed(company_profile) vs embed(client_ICP)
- Find best-matching leads

**Reference**: NLP_PATTERNS_GUIDE.md

---

## LLM Fundamentals Applied to LeadVault

### Attention Mechanism
- Focus on ICP-critical attributes when evaluating lead
- Multi-head attention captures different match types

### Fine-Tuning Approach
- **Base Model**: Claude (general knowledge)
- **Fine-tune on**: Lead datasets + sales conversion outcomes
- **Result**: Domain expert for ICP matching

### Context Window Usage
- Full company profiles
- Historical lead data
- Client ICP definition
- Sales outcomes (what converted)

**Reference**: LLM_FUNDAMENTALS_AND_TRAINING.md

---

---

## LangGraph + RAG + PEFT for LeadVault

### LangGraph (Checkpointing)
- **Backend**: PostgreSQL (research continuity)
- **Pattern**: Thread-level for multi-step company profiling
- **Recursion Limit**: 20 (deep research workflows)

### RAG Architecture
- **Documents**: Company databases, news, SEC filings, industry reports
- **Embedding**: all-mpnet-base-v2 (768-dim, strong semantic match)
- **Vector DB**: FAISS (lightweight, local deployment)

### PEFT: LoRA (Balanced)
```python
peft_config = LoraConfig(r=8, lora_alpha=32)
# Training: 3000 examples, 8GB, 6 hours
# Target: 85%+ ICP match accuracy
```

**References**: LANGGRAPH_PRODUCTION_GUIDE.md, RAG_SYSTEM_ARCHITECTURE.md, PEFT_COMPLETE_GUIDE.md

---

## LLM Architecture & Training for LeadVault

### Transformer Components
- Attention focuses on ICP-critical attributes (industry, stage, funding)
- Multi-head: revenue, growth rate, technology stack, market fit
- FFN learns company similarity patterns

### Training Pipeline
- **Pre-training**: Corporate data + market research
- **SFT**: ICP matching examples (3K pairs)
- **Alignment**: DPO + Preference tuning (prefer high-fit leads)

**References**: LLM_ARCHITECTURE_GUIDE.md, LLM_TRAINING_PIPELINE.md, LLM_ADAPTATION_GUIDE.md

---

## NLP Techniques for LeadVault

### Techniques
1. **NER**: Extract company names, industries, locations from profiles
2. **Dependency Parsing**: Understand company relationships ("works with X")
3. **Embeddings**: Semantic company similarity for clustering

### Usage
```python
nlp = NLPPipeline("leadvault")
result = nlp.process("SaaS company founded in 2020, raised Series A in AI")
# Returns: entities (SaaS, 2020, Series A), relationships
```

**Reference**: NLP_TECHNIQUES_GUIDE.md

---

**Next Step**: Apply to LeadVault codebase.
