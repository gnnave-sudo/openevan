# CSL Codebase Comparison: Local vs Remote

## Overview

| Metric | Local (Ours) | Remote (/opt/compliance-stress-lab) |
|--------|-------------|-------------------------------------|
| **Backend lines** | 4,155 | 5,579 |
| **Backend files** | 21 .py | 28 .py |
| **Frontend** | 902 HTML/JS dashboard | N/A (separate csl-web repo) |
| **Total** | 5,057 | 5,579+ |
| **Database** | SQLite (aiosqlite) | PostgreSQL (SQLAlchemy ORM) |
| **LLM** | Ollama only | Multi-provider (Gemini, Claude, OpenAI, Together, Moonshot) |
| **Auth** | None | JWT + user ownership |
| **Version** | 2.0 | 0.3.2 |

---

## Feature Matrix

| Feature | Local | Remote | Winner | Merge? |
|---------|-------|--------|--------|--------|
| **Architecture** |
| 7-layer full stack (Intake-CSL-Patterns-Alignment-Outputs-Learning-Credibility) | YES | Partial (CSL+Hermes only) | Local | Keep |
| Simulation orchestration (6-step pipeline) | Basic | Full (normalize->obligations->scenarios->agents->adjudicate->synthesize) | Remote | MERGE |
| Simulation Router (7 modes) | No | Yes (product launch, licensing, regulator letter, incident, marketing, vendor, counsel challenge) | Remote | MERGE |
| Database ORM | Basic | Full SQLAlchemy + Alembic migrations | Remote | MERGE |
| Authentication | None | JWT + user ownership | Remote | MERGE |
| **LLM Integration** |
| Ollama support | Yes | Yes (via Ollama provider) | Tie | Keep both |
| Multi-provider LLM (Gemini, Claude, OpenAI, Together, Moonshot) | No | Yes | Remote | MERGE |
| Model registry with per-agent model mapping | No | Yes | Remote | MERGE |
| Provider fallback chain | No | Yes (4-level) | Remote | MERGE |
| Structured response parsing | Basic | Advanced (JSON repair, reason-based) | Remote | MERGE |
| **CSL Engine** |
| 4-agent simulation (BA, CR, RP, NA) | Yes | Yes | Tie | Keep |
| 10-dimension risk scoring | Yes | Yes | Tie | Keep |
| Scenario templates (7 types) | No | Yes | Remote | MERGE |
| Normalized case facts step | No | Yes | Remote | MERGE |
| Obligation retrieval from DB | No | Yes | Remote | MERGE |
| JSON schema validation | No | Yes (jsonschema) | Remote | MERGE |
| Agent output validation (9 checks) | No | Yes | Remote | MERGE |
| Scoring service with weighted dimensions | Basic | Full (RiskScoringEngine class) | Remote | MERGE |
| Mock factory for testing | Basic | Advanced (prompt_loader + mock_factory) | Remote | MERGE |
| **Hermes / Pattern Layer** |
| Pattern extraction | Basic | Advanced (memory extraction + recurring patterns) | Remote | MERGE |
| Prompt improvement engine | No | Yes (prompt version tracking) | Remote | MERGE |
| Obligation proposals from simulations | No | Yes | Remote | MERGE |
| **Counsel / Alignment** |
| Counsel alignment scoring | Yes (5 dims) | Yes (via Hermes) | Local (more detailed) | Keep |
| Counsel credibility scoring (6 dims weighted) | Yes | No | Local | Keep |
| Counsel track records | Yes | Partial | Local | Keep |
| Counsel leaderboard | Yes | No | Local | Keep |
| **Management Outputs** |
| Decision memo generation | Yes | Yes | Tie | Keep best |
| Escalation list | Yes | Partial | Local | Keep |
| Control investment priorities | Yes | Partial (ControlTemplate) | Local | Keep |
| Risk heatmap | Yes | Via scoring endpoint | Local | Keep |
| **Operations** |
| Correlation ID logging | No | Yes | Remote | MERGE |
| Rate limiting | No | Yes (sliding window) | Remote | MERGE |
| Request size validation | No | Yes | Remote | MERGE |
| Response compression | No | Yes (GZip) | Remote | MERGE |
| Structured logging | No | Yes | Remote | MERGE |
| Redis caching | No | Yes | Remote | Skip (needs Redis) |
| **Frontend** |
| Dashboard | 902-line HTML/JS | Separate repo (csl-web) | Local | Keep |
| Dark theme | Yes | Unknown | Local | Keep |

---

## Merge Decision Summary

### MERGE (Remote -> Local)
1. **Multi-provider LLM client** - Gemini, Claude, OpenAI, Together, Moonshot support
2. **Simulation Router** - 7 modes for different simulation types
3. **Normalized case facts pipeline** - Proper fact normalization step
4. **Obligation retrieval** - Database-driven obligation lookup
5. **JSON schema validation** - Structured validation with jsonschema
6. **Prompt loader system** - Externalized prompt templates
7. **Mock factory** - Advanced mock data generation
8. **Correlation ID logging** - Request tracing
9. **Rate limiting** - Sliding window middleware
10. **Request size validation** - Body size enforcement
11. **Scoring service** - Weighted dimension scoring engine

### SKIP (Remote features not needed)
- PostgreSQL migration (SQLite works fine for now)
- JWT auth (can be added later)
- Redis caching (needs Redis server)
- Alembic migrations (not needed for SQLite)
- Docker Compose (local dev)

### KEEP (Local only)
- All 7 layers (Intake through Credibility)
- Counsel Credibility Scoring Model
- Standalone HTML dashboard
- Ollama integration
- SQLite persistence
