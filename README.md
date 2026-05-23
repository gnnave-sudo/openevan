# OpenEvan v10 — Autonomous Regulatory Intelligence

> The Evan Legal Quant Stack, evolved. 7-layer CSL + OpenHuman-powered autonomy: memory trees, agent loops, model routing, and voice. Built for production compliance teams.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-e92063.svg)](https://docs.pydantic.dev)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## What Changed from v2.0 → v10

OpenEvan is the next evolution of the [Evan Legal Quant Workflow Stack](https://github.com/gnnave-sudo/evan-legal-quant-stack). The v2.0 backend was a solid 7-layer API — but it was purely request/response. v10 adds **autonomous intelligence** by integrating capabilities from [OpenHuman](https://github.com/tinyhumansai/openhuman) (23.5k stars, GPL-3.0) through loose MCP-based coupling.

| Dimension | v2.0 (2024) | v10 (Now) |
|-----------|-------------|-----------|
| Architecture | FastAPI + SQLite | FastAPI + Memory Tree + Agent Loops |
| Data Layer | Flat tables | Hierarchical knowledge graph (SQLite-backed) |
| LLM Routing | Manual model selection | Auto-routed by task type (reasoning/fast/vision/code) |
| Token Efficiency | Raw text to LLM | 80% compression via TokenJuice middleware |
| Input | Manual API only | Auto-fetch from 118+ integrations (regulatory RSS, Gmail, Notion) |
| CSL Agents | Static 4-agent templates | Dynamic orchestrator with subagent role contracts |
| Background Ops | None | Subconscious monitor + 5-min heartbeat + learning loop |
| Voice/Meet | None | STT/TTS + Google Meet agent participation |
| Human Interface | HTML dashboard | Dashboard + Obsidian vault + voice |
| Interoperability | Standalone | MCP protocol — any agent can call Evan tools |

**See [`OPENHUMAN_INTEGRATION_ANALYSIS.md`](OPENHUMAN_INTEGRATION_ANALYSIS.md)** for the full deep-dive analysis with architecture diagrams, code specs, ROI projections, and 8-week implementation roadmap.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERFACES                                   │
│  Dashboard (voice+avatar) │ Obsidian Vault │ Meet Agent │ MCP API   │
├─────────────────────────────────────────────────────────────────────┤
│                       AGENT LOOP LAYER                               │
│  ┌─────────────────┐ ┌───────────────┐ ┌──────────────────────────┐ │
│  │ Subconscious    │ │ Heartbeat     │ │ Learning Loop            │ │
│  │ (continuous     │ │ (5-min tick)  │ │ (feedback adaptation)    │ │
│  │  risk monitor)  │ │ SKIP/ACT/     │ │ (weight tuning)          │ │
│  │                 │ │ ESCALATE      │ │                          │ │
│  └─────────────────┘ └───────────────┘ └──────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                       ORCHESTRATION LAYER                            │
│  Auto-fetch (20-min) → TokenJuice Compression → Model Router        │
│  → Prompt Injection Guard → Agent Orchestrator (4 subagents)        │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤
│   L1     │    L2    │    L3    │    L4    │    L5    │     L6      │
│  Intake  │ StressLab│ Patterns │ Alignment│ Outputs  │  Learning   │
│          │          │          │          │          │             │
│  Auto-   │ 4-Agent  │  Hermes  │ Counsel  │ Decision│   Drift     │
│  fetch   │ Dynamic  │  Engine  │  Memo    │  Memos  │  Tracking   │
│  Source  │ Sim      │ Extract  │ Compare  │ Heatmap │  Posture    │
│  Trees   │ Orchestrator│      │  Score   │ Escalate│  Score      │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────────┤
│                    MEMORY TREE LAYER                                 │
│  Source Trees (per regulator) → Topic Trees (per entity)             │
│  → Global Trees (per day) → Obsidian Vault (.md export)              │
├──────────┬──────────────┬──────────────┬────────────────────────────┤
│  Ollama  │  Multi-LLM   │   SQLite     │     118+ Composio           │
│  Local   │  (5 providers)│  Persistence│     Integrations            │
└──────────┴──────────────┴──────────────┴────────────────────────────┘
```

---

## The 7 Layers + Agent Infrastructure

### L1 — Regulatory Intake (Auto-fetch Enabled)
Raw regulatory ingestion with **auto-fetch from 118+ sources** via Composio. TokenJuice compresses 50-page MAS circulars to 10 pages before LLM processing. Source Trees build per-regulator knowledge automatically.

```bash
POST /api/v1/intake/raw-input          # Manual submission
GET  /api/v1/intake/auto-sources       # Configured auto-fetch sources
GET  /api/v1/intake/fact-packet/{id}   # Structured extraction
```

### L2 — Compliance Stress Lab (Dynamic Orchestration)
4-agent adversarial simulation with **dynamic orchestrator**: Business Advocate, Compliance Reviewer, Regulator Proxy, Neutral Adjudicator — each a subagent with Memory Tree access and tool usage.

```bash
POST /api/v1/stresslab/run             # Run simulation
GET  /api/v1/stresslab/result/{id}     # Results + 10-dim scoring
GET  /api/v1/stresslab/monitor         # Subconscious monitor status
```

### L3 — Pattern Extraction (Hermes + Memory Trees)
Recurring obligation tracking with **hierarchical topic trees**. Query across months of patterns naturally: *"Show me how DeFi lending risks evolved in Singapore Q1-Q2."*

### L4 — Counsel Alignment
External counsel memo comparison with **voice input** (Whisper STT) and **historical track record** via counsel Topic Trees.

### L5 — Workflow Outputs
Decision memos, risk heatmaps, escalations with **TTS reading**, **Meet agent presentation**, and **Linear/Jira auto-ticketing**.

### L6 — Continuous Learning (3-Loop Architecture)
- **Subconscious Loop**: Continuous risk monitoring, auto-triggers stress lab
- **Heartbeat Loop**: 5-min task scheduling (Skip/Act/Escalate)
- **Learning Loop**: Feedback-driven weight adaptation

### CS — Counsel Credibility Scoring
6-dimension scoring with **auto-scale detection** and **predictive accuracy** that improves with each evaluated outcome.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Ollama (optional, for local inference)
- API keys for at least one LLM provider (Gemini, Claude, OpenAI, Together, Moonshot)

### Installation

```bash
# Clone
git clone https://github.com/gnnave-sudo/openevan.git
cd openevan

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Composio for auto-fetch
pip install composio-core composio-fastapi

# Start the server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- MCP Inspector: `npx @anthropic/mcp-inspector backend/app/mcp/`

### Dashboard
Open `dashboard/index.html` in any modern browser for the standalone dark-theme dashboard with voice interface.

### Ollama Integration
```bash
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=deepseek-r1:32b  # Reasoning model for CSL
export OLLAMA_FAST_MODEL=qwen3:8b    # Fast model for intake
```

---

## Model Router: Automatic Task-to-Model Matching

OpenEvan routes LLM tasks to the optimal model automatically:

| Task Type | Hint | Primary Model | Fallback | Cost Savings |
|-----------|------|--------------|----------|-------------|
| CSL Simulation | `reasoning` | DeepSeek-R1 / Claude 3.5 | Gemini Pro | Baseline quality |
| Intake Classification | `fast` | Gemini 1.5 Flash | qwen3:8b local | 60% cheaper |
| Pattern Summarization | `summarize` | Gemma 3B local | Gemini Flash | 95% cheaper |
| PDF OCR | `vision` | GPT-4o / Gemini Pro Vision | Gemini Pro Vision | Baseline quality |
| Risk Scoring | `fast` | Gemini Flash | qwen3:8b local | 60% cheaper |
| JSON Validation | `code` | Qwen 7B local | Gemini Flash | 90% cheaper |
| Counsel Scoring | `medium` | Claude 3 Haiku | Gemini Flash | 60% cheaper |

---

## Project Structure

```
openevan/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI + agent loop orchestrator
│       ├── models.py                  # Pydantic v2 models
│       ├── database.py                # SQLite + Memory Tree layer
│       ├── routers/                   # 8 API modules
│       ├── services/                  # 12 business logic modules
│       │   ├── ollama_service.py      # Ollama local inference
│       │   ├── llm_client.py          # Multi-provider LLM client
│       │   ├── model_router.py        # Hint-based auto-routing
│       │   ├── csl_engine.py          # 4-agent simulation
│       │   ├── csl_orchestrator.py    # Dynamic agent orchestrator
│       │   ├── scoring_service.py     # 10-dim risk scoring
│       │   ├── hermes_engine.py       # Pattern extraction
│       │   ├── counsel_alignment.py   # Memo comparison
│       │   ├── output_generator.py    # Decision memo gen
│       │   ├── learning_loop.py       # Feedback adaptation
│       │   ├── credibility_model.py   # Counsel scoring
│       │   ├── normalize_case.py      # Case normalization
│       │   └── validators.py          # JSON validation
│       ├── memory/                    # Memory Tree layer
│       │   ├── tree.py                # Hierarchical tree ops
│       │   ├── chunker.py             # Semantic chunking
│       │   ├── scorer.py              # Relevance scoring
│       │   ├── vault.py               # Obsidian export
│       │   └── retriever.py           # Semantic search
│       ├── loops/                     # Agent loops
│       │   ├── subconscious.py        # Continuous monitoring
│       │   ├── heartbeat.py           # 5-min task scheduling
│       │   └── learning.py            # Feedback adaptation
│       ├── middleware/                # Request pipeline
│       │   ├── tokenjuice.py          # Token compression
│       │   └── injection_guard.py     # Prompt security
│       ├── integrations/              # External connectors
│       │   └── composio_fetcher.py    # Auto-fetch from 118+ sources
│       ├── mcp/                       # MCP protocol servers
│       │   ├── stresslab_server.py    # CSL as MCP tool
│       │   ├── credibility_server.py  # Scoring as MCP tool
│       │   └── patterns_server.py     # Patterns as MCP tool
│       ├── voice/                     # Voice interface
│       │   ├── stt.py                 # Whisper local STT
│       │   └── tts.py                 # Piper/ElevenLabs TTS
│       ├── meet/                      # Meet agent
│       │   └── agent.py               # Google Meet participation
│       └── utils/
│           ├── prompt_loader.py       # External prompt templates
│           └── mock_factory.py        # Test data generation
├── dashboard/
│   └── index.html                     # Voice-enabled dark dashboard
├── OPENHUMAN_INTEGRATION_ANALYSIS.md  # Full integration deep-dive
├── CSL_COMPARISON.md                  # CSL v1 vs v2 comparison
├── e2e_test.py                        # 47-assertion E2E suite
├── mock_ollama_server.py              # Mock Ollama for testing
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

> **Note on directory structure:** The `memory/`, `loops/`, `middleware/`, `integrations/`, `mcp/`, `voice/`, and `meet/` directories contain the v10 OpenHuman-inspired enhancements. These are being implemented incrementally per the 8-week roadmap in [`OPENHUMAN_INTEGRATION_ANALYSIS.md`](OPENHUMAN_INTEGRATION_ANALYSIS.md). The core `services/` and `routers/` are production-ready now.

---

## Testing

```bash
# Full E2E test suite (47 assertions, no external deps)
python e2e_test.py

# With live Ollama
export OLLAMA_HOST=http://localhost:11434
export E2E_LIVE_LLM=1
python e2e_test.py

# MCP server test
python -m pytest backend/app/mcp/ -v
```

---

## TokenJuice: Universal Compression

Every LLM-bound request passes through TokenJuice middleware:

```python
# Before: 50-page MAS circular at ~15,000 tokens → $0.40
# After:  TokenJuice compressed to ~3,000 tokens → $0.08

# Regulatory rule overlay examples:
# "Anti-Money Laundering" → "AML"
# "Monetary Authority of Singapore" → "MAS"
# "Virtual Asset Service Provider" → "VASP"
# Plus: HTML→Markdown, URL shortening, deduplication
```

**Savings: ~$12,000/year at 100 documents/day processing volume.**

---

## MCP Protocol: Cross-Agent Interoperability

OpenEvan exposes all 7 layers as MCP tools. Any MCP-compatible agent can discover and call them:

```json
{
  "mcpServers": {
    "openevan-stresslab": {
      "command": "python",
      "args": ["-m", "backend.app.mcp.stresslab_server"]
    },
    "openevan-credibility": {
      "command": "python",
      "args": ["-m", "backend.app.mcp.credibility_server"]
    }
  }
}
```

Compatible with: Claude Desktop, Cursor, OpenHuman, any MCP client.

---

## 8-Week Implementation Roadmap

| Phase | Weeks | Score | Deliverables |
|-------|-------|-------|-------------|
| **Foundation** | 1-2 | 7/10 | TokenJuice middleware, Model Router, Prompt Injection Guard |
| **Memory** | 3-4 | 8/10 | Memory Tree layer, Obsidian vault, MCP servers |
| **Autonomy** | 5-6 | 9/10 | Auto-fetch, Agent Orchestrator, Subconscious + Heartbeat loops |
| **Voice & Presence** | 7-8 | **10/10** | STT/TTS, Dashboard avatar, Meet agent, Learning loop |

See [`OPENHUMAN_INTEGRATION_ANALYSIS.md`](OPENHUMAN_INTEGRATION_ANALYSIS.md) for detailed technical specs, code samples, and ROI projections for each phase.

---

## License

**MIT License** — The OpenEvan codebase is MIT licensed. OpenHuman integration is achieved through loose MCP-protocol coupling, avoiding GPL-3.0 contamination. The OpenHuman components remain separate processes.

---

**From API backend to autonomous regulatory intelligence. v10 is just the beginning.**
