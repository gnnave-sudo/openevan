# OpenEvan v11 — Merged Unified Compliance Intelligence

> The Evan Legal Quant Stack, merged with x870's Evan-AI Compliance OS. 98 endpoints across 16 domains. The most complete open-source regulatory intelligence platform.

**v11 Update (2026-05-23):** Merged with the running x870 Evan-AI API (62 endpoints: Chat, Matters, Documents, Memory, Drafts, Research) + OpenEvan Analytical Engine (36 endpoints: CSL Stress Lab, Patterns, Credibility, Alignment, Learning, Intake). See [`MERGE_ANALYSIS.md`](MERGE_ANALYSIS.md) for the full merge deep-dive.

---

**Previous: [v10 README](https://github.com/gnnave-sudo/openevan/tree/v10#readme)** — 7-layer CSL + OpenHuman-powered autonomy roadmap

---

## Quick Stats

| | v10 (Original) | x870 (Discovered) | v11 (Merged) |
|---|---|---|---|
| **Endpoints** | 30 | 62 | **98** |
| **Domains** | 7 layers | 10 domains | **16 domains** |
| **Models** | 15 | 40 | **55** |
| **Database Tables** | 7 | 13 | **20** |
| **Code Lines** | ~9,000 | — | **+3,300 new** |

## What's New in v11

### x870 Integration ( discovered on gnnave-x870.tail8e40c8.ts.net )

The x870 server was running a separate **Evan-AI Compliance Operating System** with these capabilities now merged:

- **Chat** — Streaming + session-based conversational interface
- **Matters** — Full matter lifecycle (CRUD, events, timeline, deadlines)
- **Documents** — Upload, chunk, URL ingest, matter linking
- **Memory** — CRUD + semantic search + human approval queue
- **Drafts** — 6 types: management-brief, email, weekly-update, regulator-response, decision-card, meeting-minutes
- **Research** — Query + monitoring agents
- **Tasks** — Task management with blockers
- **Stakeholders** — Stakeholder profiles with tone analysis
- **Precedents** — Searchable precedent library
- **Outputs** — Approval workflow with feedback and promote-to-precedent

### OpenEvan Analytical Engine

- **L1 Intake** — Regulatory text → structured FactPackets
- **L2 CSL Stress Lab** — 4-agent simulation, 7 modes, 10-dim risk scoring
- **L3 Patterns** — Hermes engine: recurring obligations, risk drivers
- **L4 Alignment** — Counsel memo comparison, 5-dim scoring
- **L6 Learning** — Posture scoring, drift timeline, historical comparison
- **CS Credibility** — 6-dimension counsel scoring, tier classification

## Merged Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     USER EXPERIENCE LAYER                         │
│  Chat │ Matters │ Documents │ Memory │ Drafts │ Tasks │ Research  │
├──────────────────────────────────────────────────────────────────┤
│                    INTELLIGENCE LAYER                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ L1 Intake│ │ L2 CSL   │ │ L3 Patterns│ │ CS Credibility   │   │
│  │ L4 Align │ │ L5 Output│ │ L6 Learning│ │ Precedents       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│                    FOUNDATION LAYER                               │
│  Multi-LLM │ Model Router │ SQLite │ 20 Tables │ MCP Tools       │
└──────────────────────────────────────────────────────────────────┘
```

## Merged Directory Structure

```
openevan/
├── backend/              # Original v10 backend (7 layers + CSL)
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── database.py
│       ├── services/     # 12 service modules
│       ├── routers/      # 8 API routers
│       └── utils/
├── merged/               # NEW: v11 unified API (x870 + OpenEvan)
│   └── app/
│       ├── main.py       # 834 lines, 62 x870 endpoints
│       ├── models.py     # 604 lines, 55 schemas
│       ├── database.py   # 437 lines, 20 tables
│       ├── routers/      # 6 OpenEvan routers, 36 endpoints
│       └── requirements.txt
├── dashboard/            # Standalone HTML dashboard
├── MERGE_ANALYSIS.md     # Full merge deep-dive
└── OPENHUMAN_INTEGRATION_ANALYSIS.md  # OpenHuman integration plan
```

## Deploy the Merged API

```bash
git clone https://github.com/gnnave-sudo/openevan.git
cd openevan/merged
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

*Below is the original v10 README for reference...*

---

