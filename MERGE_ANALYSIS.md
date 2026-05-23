# OpenEvan x870 Merge Analysis: Two Systems, One Super-Stack

## Discovery: x870 Runs a DIFFERENT Evan-AI API

The gnnave-x870 server is already running an **Evan-AI Compliance Operating System** at port 8000 with 62 endpoints across 10 domains. Our OpenEvan v10 stack is a separate codebase. The two systems are **complementary, not overlapping**.

---

## System A: x870 Evan-AI API (Running Now)

**62 endpoints, 40 schemas, 10 domains**

| Domain | Endpoints | What It Does |
|--------|-----------|-------------|
| **Chat** | 5 | Streaming + session-based conversational interface |
| **Matters** | 7 | Full matter lifecycle (CRUD, events, timeline, deadlines, snapshots, summaries) |
| **Documents** | 5 | Upload, chunk, URL ingest, matter linking |
| **Memory** | 7 | CRUD + semantic search + approval queue (human-in-the-loop) |
| **Preferences** | 3 | User preference learning with confirmation |
| **Outputs** | 4 | Output approval, feedback, promote-to-precedent |
| **Precedents** | 3 | Searchable precedent library |
| **Tasks** | 3 | Task management with blockers |
| **Stakeholders** | 3 | Stakeholder profiles with tone analysis |
| **Drafts** | 6 | Management brief, email, weekly-update, regulator-response, decision-card, meeting-minutes |
| **Research** | 2 | Research query + monitoring |
| **Admin** | 2 | Audit log, metrics |

**Strengths:** Conversational UX, matter management, document intelligence, human-in-the-loop approval queues, precedent library, stakeholder tracking, research monitoring, streaming chat.

**Weaknesses:** No CSL stress lab, no risk scoring engine, no pattern extraction, no credibility scoring, no regulatory intake pipeline, no learning loop, no model routing.

---

## System B: OpenEvan v10 (Our Stack)

**41 source files, ~9K lines, 7+1 layers**

| Layer | What It Does |
|-------|-------------|
| **L1 Intake** | Raw regulatory text → structured FactPackets (jurisdiction, obligations, controls) |
| **L2 CSL Stress Lab** | 4-agent adversarial simulation, 7 modes, 10-dimension weighted risk scoring |
| **L3 Patterns** | Hermes engine: recurring obligation extraction, risk pattern library |
| **L4 Counsel Alignment** | External counsel memo comparison, 5-dim alignment scoring |
| **L5 Outputs** | Decision memos, risk heatmaps, escalation lists (P0/P1/P2) |
| **L6 Learning** | Drift tracking, posture scoring, historical comparison |
| **CS Credibility** | 6-dimension counsel credibility scoring with tier classification |

**Strengths:** Deep regulatory intelligence, quantitative risk analysis, adversarial simulation, pattern extraction, credibility scoring, 47/47 E2E tests, multi-provider LLM with model routing, TokenJuice compression.

**Weaknesses:** No conversational interface, no matter management, no document chunking, no human approval queues, no precedent library, no stakeholder tracking, no streaming, no research monitoring.

---

## The Merge: Unified OpenEvan v11

### Strategy: x870 as the Foundation, OpenEvan as the Engine

The x870 API has the **UX layer** (chat, streaming, sessions, matters, documents, approval queues). OpenEvan has the **analytical engine** (CSL, risk scoring, patterns, credibility, learning loops). The merge injects OpenEvan's analytical capabilities INTO x870's conversational/matter framework.

### Merged Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    USER EXPERIENCE LAYER (x870)                       │
│  Chat (streaming) │ Matters │ Documents │ Tasks │ Stakeholders       │
│  Memory (approval Q) │ Precedents │ Outputs (approval) │ Research    │
├──────────────────────────────────────────────────────────────────────┤
│                    INTELLIGENCE LAYER (OpenEvan)                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐ │
│  │ L1 Intake  │ │ L2 CSL     │ │ L3 Patterns│ │ CS Credibility   │ │
│  │ Regulatory │ │ Stress Lab │ │ Hermes     │ │ Scoring          │ │
│  │ FactPacket │ │ 4-Agent    │ │ Engine     │ │ 6-Dimension      │ │
│  │ Extraction │ │ Simulation │ │ Extraction │ │ Tier Classification│ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ L4 Counsel Alignment │ L5 Outputs │ L6 Continuous Learning     │ │
│  │ Memo Comparison      │ Heatmaps   │ Drift Tracking              │ │
│  │ 5-Dim Scoring        │ Escalations│ Posture Scoring             │ │
│  └────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│                    FOUNDATION LAYER (merged)                          │
│  Multi-LLM Client │ Model Router │ TokenJuice │ SQLite │ MCP Tools   │
│  Ollama Local     │ 5 Providers  │ Compress   │ Memory │ 118+ Ints  │
└──────────────────────────────────────────────────────────────────────┘
```

### New Unified Endpoints

| Domain | x870 Endpoints | OpenEvan Additions | Merged Total |
|--------|---------------|-------------------|--------------|
| Chat | 5 | + stresslab chat, + pattern chat, + credibility chat | 8 |
| Matters | 7 | + risk score, + CSL trigger, + alignment link | 10 |
| Documents | 5 | + fact packet extraction, + L1 intake | 7 |
| Memory | 7 | + pattern library, + drift timeline | 9 |
| Preferences | 3 | (keep as-is) | 3 |
| Outputs | 4 | + risk heatmap, + escalation list | 6 |
| Precedents | 3 | (keep, link to patterns) | 3 |
| Tasks | 3 | + auto-create from escalations | 4 |
| Stakeholders | 3 | + credibility score link | 4 |
| Drafts | 6 | + CSL-aware drafting | 6 |
| Research | 2 | + regulatory source auto-fetch | 3 |
| **Stress Lab** | — | **NEW: Full CSL** | **8** |
| **Patterns** | — | **NEW: Hermes + risk index** | **5** |
| **Credibility** | — | **NEW: Full scoring system** | **4** |
| **Alignment** | — | **NEW: Counsel comparison** | **4** |
| **Learning** | — | **NEW: Drift + posture** | **4** |
| **Admin** | 2 | + model router status, + tokenjuice stats | 4 |
| **TOTAL** | **62** | **+45 new** | **~107** |

### Integration Points

1. **Matter ↔ CSL**: Every matter with `risk_score > 70` auto-triggers CSL simulation. Results stored as matter events.
2. **Document ↔ L1 Intake**: Uploaded regulatory documents auto-extract FactPackets via L1 pipeline.
3. **Chat ↔ All Layers**: Conversational interface can invoke any OpenEvan layer via function calling.
4. **Output ↔ Escalation**: P0 outputs auto-create tasks with blockers.
5. **Memory ↔ Pattern Library**: Approved memory items feed Hermes pattern extraction.
6. **Stakeholder ↔ Credibility**: External counsel stakeholders get credibility scores.
7. **Research ↔ Auto-fetch**: Research monitors pull from regulatory RSS via Composio.

### Files to Create for Merge

| File | Description | Lines |
|------|-------------|-------|
| `merged/main.py` | Unified FastAPI app (x870 base + OpenEvan routers) | ~350 |
| `merged/models.py` | Merged Pydantic models | ~400 |
| `merged/database.py` | Unified SQLite schema | ~500 |
| `merged/services/stresslab_service.py` | CSL engine adapted for matter context | ~350 |
| `merged/services/pattern_service.py` | Hermes + memory integration | ~250 |
| `merged/services/credibility_service.py` | Counsel scoring with stakeholder link | ~200 |
| `merged/services/alignment_service.py` | Memo alignment with document link | ~200 |
| `merged/services/learning_service.py` | Drift + posture tracking | ~200 |
| `merged/services/intake_service.py` | L1 regulatory intake | ~250 |
| `merged/routers/stresslab.py` | 8 new endpoints | ~150 |
| `merged/routers/patterns.py` | 5 new endpoints | ~120 |
| `merged/routers/credibility.py` | 4 new endpoints | ~100 |
| `merged/routers/alignment.py` | 4 new endpoints | ~100 |
| `merged/routers/learning.py` | 4 new endpoints | ~100 |
| `merged/routers/intake.py` | 4 new endpoints | ~100 |
| **TOTAL** | **16 files** | **~3,370 lines** |

---

## Deployment Strategy

1. **Phase 1**: Deploy alongside existing API on different port (8001)
2. **Phase 2**: Verify all new endpoints work with x870's existing data
3. **Phase 3**: Merge into unified app on port 8000 (replace)
4. **Phase 4**: Update dashboard to cover all 107 endpoints

---

*Analysis generated 2026-05-23. x870 spec: 62 endpoints, 40 schemas. OpenEvan v10: 41 files, 7+1 layers.*
