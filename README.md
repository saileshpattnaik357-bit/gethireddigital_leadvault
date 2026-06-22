# LeadVault Agentic AI Engine

Standalone agentic AI lead-mining application.

LeadVault takes a client ICP, service list, positioning, website, and target audience, then generates a client-specific mining brain:

- buyer intent clusters
- LinkedIn search queries
- Google/Serp-style queries
- buyer phrases
- negative filters
- Python-ready query bank
- confirmed mining execution with Apify/public-web budget controls
- accepted and rejected lead/debug outputs

LeadVault can operate independently and can also be called by DIGIX as an ecosystem module.

## Local Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

Add real Apify tokens only to `backend/.env`:

```env
APIFY_API_TOKENS=token1,token2
```

## Local Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## API

- `POST /api/leadvault/plan`
- `POST /api/leadvault/upload`
- `GET /api/leadvault/specs`
- `POST /api/leadvault/mine`
- `POST /api/leadvault/mine-upload`
- `POST /api/leadvault/linkedin-capture`
- `POST /api/leadvault/linkedin-capture-upload`

Mining requires `confirmed=true`.

## DIGIX Integration

DIGIX should call LeadVault through HTTP as a separate engine:

```text
DIGIX -> LeadVault API -> mining brain / mining run / accepted leads
```

The LeadVault core should not depend on DIGIX internals.
