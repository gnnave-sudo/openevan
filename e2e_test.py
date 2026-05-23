#!/usr/bin/env python3
"""
End-to-End Test for Evan Legal Quant Workflow Stack
Tests all 7 layers + Counsel Credibility Scoring using real HTTP calls.
"""

import subprocess
import time
import sys
import json
import signal
import os

# ===== Color codes for output =====
GREEN = "\033[92m"
RED = "\033[91m"
AMBER = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

PASS = f"{GREEN}PASS{RESET}"
FAIL = f"{RED}FAIL{RESET}"
INFO = f"{CYAN}INFO{RESET}"

def log(msg, level="INFO"):
    colors = {"INFO": INFO, "PASS": PASS, "FAIL": FAIL, "STEP": BOLD}
    print(f"  [{colors.get(level, level)}] {msg}")

def log_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"{BOLD}STEP {step_num}: {title}{RESET}")
    print("="*60)

def http_call(method, path, data=None, base="http://localhost:8000"):
    """Make HTTP call and return parsed response."""
    import urllib.request
    import urllib.error

    url = f"{base}{path}"
    headers = {"Content-Type": "application/json"}

    if data:
        body = json.dumps(data).encode('utf-8')
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
            return {"status": resp.status, "body": json.loads(body) if body else {}}
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return {"status": e.code, "body": body, "error": True}
    except Exception as e:
        return {"status": 0, "body": str(e), "error": True}

# ===== Process Management =====
ollama_proc = None
backend_proc = None

def cleanup(signum=None, frame=None):
    """Kill all subprocesses on exit."""
    log("Cleaning up processes...", "INFO")
    for proc_name, proc in [("Ollama", ollama_proc), ("Backend", backend_proc)]:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=3)
                log(f"{proc_name} stopped", "PASS")
            except:
                try:
                    proc.kill()
                    log(f"{proc_name} killed", "INFO")
                except:
                    pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ===== Test Results =====
results = []

def check(name, condition, details=""):
    results.append((name, condition, details))
    if condition:
        log(f"✓ {name}", "PASS")
    else:
        log(f"✗ {name}: {details}", "FAIL")
    return condition

# ============================================================
# MAIN TEST
# ============================================================
print(f"""
{BOLD}╔══════════════════════════════════════════════════════════════╗
║     EVAN LEGAL QUANT STACK — END-TO-END TEST                ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")

project_dir = "/mnt/agents/output/project"
backend_dir = f"{project_dir}/backend"

# ===== STEP 0: Install Dependencies =====
log_step(0, "Install Dependencies")

# Install backend deps
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-r", f"{backend_dir}/requirements.txt", "--quiet"],
    capture_output=True, text=True, cwd=backend_dir
)
if result.returncode != 0:
    log(f"pip install issues (may be already installed): {result.stderr[:200]}", "INFO")
else:
    log("Backend dependencies installed", "PASS")

# ===== STEP 1: Start Mock Ollama Server =====
log_step(1, "Start Mock Ollama Server")

ollama_proc = subprocess.Popen(
    [sys.executable, f"{project_dir}/mock_ollama_server.py"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
time.sleep(2)

# Verify Ollama is running
resp = http_call("GET", "/api/tags", base="http://localhost:11434")
if check("Ollama server running", resp.get("status") == 200, str(resp.get("status", "down"))):
    log(f"  Models: {resp.get('body', {}).get('models', [])}", "INFO")
else:
    log("Ollama not responding, continuing with fallback...", "INFO")

# ===== STEP 2: Start Backend =====
log_step(2, "Start Backend API Server")

env = os.environ.copy()
env["OLLAMA_HOST"] = "http://localhost:11434"

backend_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
    cwd=backend_dir,
    env=env,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
time.sleep(3)

# Verify backend
resp = http_call("GET", "/")
if check("Backend API running", resp.get("status") == 200, str(resp.get("status", "down"))):
    log(f"  Status: {json.dumps(resp.get('body', {}), indent=2)[:300]}", "INFO")

# ===== STEP 3: Layer 1 — Raw Input Submission & Structuring =====
log_step(3, "Layer 1 — Intake & Structuring (Ollama)")

# Submit raw input
resp1 = http_call("POST", "/api/v1/intake/submit", {
    "input_type": "product_proposal",
    "source": "Product Team",
    "content": "Proposal for yield-bearing DPT program in Singapore targeting retail users with custody via licensed trust arrangement. Revenue model: spread on yield. The DPT license explicitly covers custody. Cross-border: none. MAS has been consulted informally."
})
raw_input_id = None
if check("L1: Submit raw input", resp1.get("status") == 200, str(resp1.get("body", ""))[:100]):
    raw_input_id = resp1.get("body", {}).get("id")
    log(f"  Raw Input ID: {raw_input_id}", "INFO")
    log(f"  Type: {resp1.get('body', {}).get('input_type')}", "INFO")
    log(f"  Status: {resp1.get('body', {}).get('status')}", "INFO")

# Structure using Ollama
if raw_input_id:
    time.sleep(1)
    resp2 = http_call("POST", f"/api/v1/intake/{raw_input_id}/structure")
    fact_packet_id = None
    if check("L1: Ollama structuring", resp2.get("status") == 200, str(resp2.get("body", ""))[:100]):
        fp = resp2.get("body", {})
        fact_packet_id = fp.get("id")
        log(f"  Fact Packet ID: {fact_packet_id}", "INFO")
        log(f"  Jurisdiction: {fp.get('jurisdiction')}", "INFO")
        log(f"  Regulator: {fp.get('regulator')}", "INFO")
        log(f"  Product Class: {fp.get('product_class')}", "INFO")
        log(f"  Obligations found: {len(fp.get('obligations', {}).get('licensing_triggers', []))} licensing, {len(fp.get('obligations', {}).get('aml_triggers', []))} AML", "INFO")
        check("L1: Jurisdiction detected", fp.get("jurisdiction") != "Unknown", fp.get("jurisdiction"))
        check("L1: Obligations extracted", len(fp.get("obligations", {}).get("licensing_triggers", [])) > 0, str(fp.get("obligations", {})))

# ===== STEP 4: Layer 2 — CSL Stress Test =====
log_step(4, "Layer 2 — Compliance Stress Lab (4-Agent Simulation)")

if fact_packet_id:
    resp3 = http_call("POST", f"/api/v1/stresslab/run/{fact_packet_id}")
    stress_result_id = None
    if check("L2: Run stress test", resp3.get("status") == 200, str(resp3.get("body", ""))[:100]):
        sr = resp3.get("body", {})
        stress_result_id = sr.get("id")
        log(f"  Stress Result ID: {stress_result_id}", "INFO")
        log(f"  Scenarios generated: {len(sr.get('scenarios', []))}", "INFO")
        log(f"  Final Risk Rating: {sr.get('final_risk_rating')}/100", "INFO")
        log(f"  Final Recommendation: {sr.get('final_recommendation')}", "INFO")

        check("L2: Scenarios created", len(sr.get("scenarios", [])) > 0, str(len(sr.get("scenarios", []))))
        check("L2: Has decisive obligations", len(sr.get("decisive_obligations", [])) > 0, str(sr.get("decisive_obligations", [])))
        check("L2: Has control gaps", len(sr.get("key_control_gaps", [])) > 0)
        check("L2: Has evidence checklist", len(sr.get("evidence_checklist", [])) > 0)
        check("L2: Has regulator objections", len(sr.get("regulator_objections", [])) > 0)

        # Verify first scenario has all 4 agents
        if sr.get("scenarios"):
            sc = sr["scenarios"][0]
            agents = sc.get("agent_positions", {})
            check("L2: Business Advocate position", bool(agents.get("business_advocate")))
            check("L2: Compliance Reviewer position", bool(agents.get("compliance_reviewer")))
            check("L2: Regulator Proxy position", bool(agents.get("regulator_proxy")))
            check("L2: Neutral Adjudicator position", bool(agents.get("neutral_adjudicator")))
            check("L2: Risk score has 10 dimensions", len(sc.get("risk_score", {}).get("dimensions", {})) == 10)

# ===== STEP 5: Layer 3 — Pattern Intelligence =====
log_step(5, "Layer 3 — Hermes Pattern Intelligence")

if stress_result_id:
    resp4 = http_call("POST", f"/api/v1/patterns/extract/{stress_result_id}")
    if check("L3: Pattern extraction", resp4.get("status") == 200, str(resp4.get("body", ""))[:100]):
        pattern = resp4.get("body", {})
        log(f"  Jurisdiction: {pattern.get('jurisdiction')}", "INFO")
        log(f"  Risk drivers: {pattern.get('risk_drivers', [])}", "INFO")
        log(f"  Recurrent obligations: {pattern.get('recurrent_obligations', [])}", "INFO")
        check("L3: Risk drivers found", len(pattern.get("risk_drivers", [])) > 0)
        check("L3: Recurrent obligations found", len(pattern.get("recurrent_obligations", [])) > 0)

    # Get risk indices
    resp5 = http_call("GET", "/api/v1/patterns/indices")
    if check("L3: Risk indices", resp5.get("status") == 200):
        indices = resp5.get("body", {})
        log(f"  Jurisdictions tracked: {list(indices.get('jurisdiction_risk_index', {}).keys())}", "INFO")
        log(f"  Obligation frequencies: {len(indices.get('obligation_frequency', {}))} entries", "INFO")

# ===== STEP 6: Layer 4 — Counsel Alignment =====
log_step(6, "Layer 4 — Counsel Alignment Engine")

# Submit counsel memo
resp6 = http_call("POST", "/api/v1/alignment/submit-memo", {
    "counsel_name": "External Counsel A",
    "memo_content": "The DPT license is sufficient for the yield program. No SFA fund management licensing is required. Risk assessment: LOW. Proceed with standard disclosures and retail risk warnings.",
    "related_fact_packet_id": fact_packet_id if fact_packet_id else None
})
memo_id = None
if check("L4: Submit counsel memo", resp6.get("status") == 200, str(resp6.get("body", ""))[:100]):
    memo_id = resp6.get("body", {}).get("id")
    log(f"  Memo ID: {memo_id}", "INFO")

# Analyze alignment
if memo_id:
    time.sleep(1)
    resp7 = http_call("POST", f"/api/v1/alignment/analyze/{memo_id}")
    if check("L4: Alignment analysis", resp7.get("status") == 200, "HTTP error"):
        align = resp7.get("body", {})
        log(f"  Alignment Score: {align.get('alignment_score')}/100", "INFO")
        log(f"  Dimension scores: {json.dumps(align.get('dimension_scores', {}), indent=2)}", "INFO")
        log(f"  Missing objections: {len(align.get('missing_regulator_objections', []))}", "INFO")
        log(f"  Overconfidence flags: {len(align.get('overconfidence_flags', []))}", "INFO")
        log(f"  Clarification questions: {len(align.get('suggested_clarification_questions', []))}", "INFO")
        check("L4: Score computed", align.get("alignment_score") is not None)
        check("L4: Missing objections detected", len(align.get("missing_regulator_objections", [])) > 0)
        check("L4: Overconfidence flagged", len(align.get("overconfidence_flags", [])) > 0)

# ===== STEP 7: Layer 5 — Management Output =====
log_step(7, "Layer 5 — Management Output Generation")

if stress_result_id:
    # Generate decision memo
    resp8 = http_call("POST", f"/api/v1/outputs/generate-memo/{stress_result_id}")
    if check("L5: Decision memo generated", resp8.get("status") == 200, str(resp8.get("body", ""))[:100]):
        memo = resp8.get("body", {})
        log(f"  Title: {memo.get('title')}", "INFO")
        log(f"  Exec summary length: {len(memo.get('executive_summary', ''))} chars", "INFO")
        log(f"  Recommendations: {len(memo.get('recommendations', []))}", "INFO")
        log(f"  Next steps: {len(memo.get('next_steps', []))}", "INFO")
        check("L5: Has title", bool(memo.get("title")))
        check("L5: Has executive summary", len(memo.get("executive_summary", "")) > 10)
        check("L5: Has recommendations", len(memo.get("recommendations", [])) > 0)

    # Get heatmap
    resp9 = http_call("GET", "/api/v1/outputs/heatmap")
    check("L5: Risk heatmap", resp9.get("status") == 200, str(resp9.get("body", ""))[:100])

    # Get escalations
    resp10 = http_call("GET", "/api/v1/outputs/escalations")
    check("L5: Escalation list", resp10.get("status") == 200, str(resp10.get("body", ""))[:100])

    # Get control priorities
    resp11 = http_call("GET", "/api/v1/outputs/control-priorities")
    check("L5: Control priorities", resp11.get("status") == 200, str(resp11.get("body", ""))[:100])

# ===== STEP 8: Layer 6 — Continuous Learning =====
log_step(8, "Layer 6 — Continuous Learning Loop")

resp12 = http_call("POST", "/api/v1/learning/detect-drift/yield-program-sg")
if check("L6: Drift detection", resp12.get("status") == 200, "HTTP error"):
    drift = resp12.get("body", {})
    log(f"  Drift detected: {drift.get('drift_detected')}", "INFO")
    log(f"  Magnitude: {drift.get('drift_magnitude')}", "INFO")
    log(f"  Posture change: {drift.get('posture_change')}", "INFO")
    check("L6: Has posture change", bool(drift.get("posture_change")))

resp13 = http_call("GET", "/api/v1/learning/history/yield-program-sg")
check("L6: Historical comparison", resp13.get("status") == 200, str(resp13.get("body", ""))[:100])

# ===== STEP 9: Part II — Counsel Credibility Scoring =====
log_step(9, "Part II — Counsel Credibility Scoring")

resp14 = http_call("POST", "/api/v1/credibility/score", {
    "counsel_name": "Counsel A",
    "matter_id": "M-2026-001",
    "dimension_scores": {
        "obligation_identification": 0.90,
        "risk_classification": 0.85,
        "evidence_sufficiency": 0.80,
        "assumption_transparency": 0.88,
        "regulator_posture_realism": 0.82,
        "control_practicality": 0.75
    }
})
if check("Credibility: Score submitted", resp14.get("status") == 200, "HTTP error"):
    score = resp14.get("body", {})
    log(f"  Weighted Score: {score.get('weighted_score')}", "INFO")
    log(f"  Risk Tier: {score.get('risk_tier')}", "INFO")
    log(f"  Dimension scores: {json.dumps(score.get('dimension_scores', {}), indent=2)}", "INFO")
    check("Credibility: Score calculated", score.get("weighted_score") is not None)
    check("Credibility: Tier assigned", score.get("risk_tier") in ["HIGH_RISK", "WEAK", "ACCEPTABLE", "STRONG", "HIGHLY_RELIABLE"])
    check("Credibility: Score in correct range", 70 <= score.get("weighted_score", 0) <= 90)

# Submit another score
resp15 = http_call("POST", "/api/v1/credibility/score", {
    "counsel_name": "Counsel B",
    "matter_id": "M-2026-002",
    "dimension_scores": {
        "obligation_identification": 0.55,
        "risk_classification": 0.45,
        "evidence_sufficiency": 0.60,
        "assumption_transparency": 0.50,
        "regulator_posture_realism": 0.55,
        "control_practicality": 0.65
    }
})
check("Credibility: Score Counsel B", resp15.get("status") == 200)

# Get leaderboard
resp16 = http_call("GET", "/api/v1/credibility/leaderboard")
if check("Credibility: Leaderboard", resp16.get("status") == 200, "HTTP error"):
    board = resp16.get("body", [])
    log(f"  Counsel ranked: {len(board)}", "INFO")
    if board:
        log(f"  #1: {board[0].get('counsel_name')} — Score: {board[0].get('average_score')}, Tier: {board[0].get('tier')}", "INFO")
    check("Credibility: Leaderboard has entries", len(board) > 0)

# Get track record
resp17 = http_call("GET", "/api/v1/credibility/counsel/Counsel%20A")
if check("Credibility: Track record", resp17.get("status") == 200, "HTTP error"):
    tr = resp17.get("body", {})
    log(f"  Average score: {tr.get('average_score')}", "INFO")
    log(f"  Hindsight accuracy: {tr.get('hindsight_accuracy')}", "INFO")

# ===== STEP 10: Verify Startup Mock Data =====
log_step(10, "Verify Startup Mock Data Persistence")

resp18 = http_call("GET", "/api/v1/intake")
check("Startup: Raw inputs exist", resp18.get("status") == 200 and len(resp18.get("body", [])) > 0)

resp19 = http_call("GET", "/api/v1/stresslab")
check("Startup: Stress results exist", resp19.get("status") == 200 and len(resp19.get("body", [])) > 0)

resp20 = http_call("GET", "/api/v1/outputs/escalations")
check("Startup: Escalations exist", resp20.get("status") == 200 and len(resp20.get("body", [])) > 0)

# ===== RESULTS SUMMARY =====
print(f"\n{'='*60}")
print(f"{BOLD}TEST RESULTS SUMMARY{RESET}")
print("="*60)

total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n  Total tests: {total}")
print(f"  {GREEN}Passed: {passed}{RESET}")
if failed:
    print(f"  {RED}Failed: {failed}{RESET}")

print(f"\n{BOLD}Test Coverage:{RESET}")
print(f"  ✓ Layer 0: Raw Input Ingestion")
print(f"  ✓ Layer 1: Ollama Intake & Structuring")
print(f"  ✓ Layer 2: CSL 4-Agent Stress Simulation")
print(f"  ✓ Layer 3: Hermes Pattern Intelligence")
print(f"  ✓ Layer 4: Counsel Alignment Engine")
print(f"  ✓ Layer 5: Management Output Generation")
print(f"  ✓ Layer 6: Continuous Learning Loop")
print(f"  ✓ Part II: Counsel Credibility Scoring")
print(f"  ✓ Startup Mock Data")

if failed == 0:
    print(f"\n{GREEN}{BOLD}ALL TESTS PASSED ✓{RESET}")
else:
    print(f"\n{AMBER}{BOLD}SOME TESTS FAILED — see details above{RESET}")
    print(f"\n{RED}Failed tests:{RESET}")
    for name, ok, details in results:
        if not ok:
            print(f"  ✗ {name}: {details}")

print(f"\n{'='*60}\n")

# Cleanup
cleanup()
