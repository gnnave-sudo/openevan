#!/bin/bash
# Quick verification script for Evan Legal Quant Stack

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'
PASS=0
FAIL=0

check() {
    if eval "$2" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

echo "========================================"
echo "  Evan Legal Quant — Verification"
echo "========================================"

# Process checks
check "evan-ollama service exists" "systemctl list-unit-files | grep evan-ollama"
check "evan-backend service exists" "systemctl list-unit-files | grep evan-backend"
check "Ollama port 11434 listening" "ss -tlnp | grep :11434"
check "Backend port 8000 listening" "ss -tlnp | grep :8000"

# API checks
check "Backend / returns operational" "curl -s http://localhost:8000/ | grep -q operational"
check "Backend has 11 layers active" "curl -s http://localhost:8000/ | grep -q 'Compliance Stress Lab'"
check "Intake submit works" "curl -s -X POST http://localhost:8000/api/v1/intake/submit -H 'Content-Type: application/json' -d '{\"input_type\":\"test\",\"source\":\"verify\",\"content\":\"test\"}' | grep -q id"
check "Stress lab list works" "curl -s http://localhost:8000/api/v1/stresslab | grep -q scenarios"
check "Patterns indices works" "curl -s http://localhost:8000/api/v1/patterns/indices | grep -q jurisdiction"
check "Escalations works" "curl -s http://localhost:8000/api/v1/outputs/escalations | grep -q title"
check "Credibility leaderboard works" "curl -s http://localhost:8000/api/v1/credibility/leaderboard | grep -q counsel_name"
check "Simulation modes works" "curl -s http://localhost:8000/api/v1/stresslab/modes | grep -q product_launch"

echo ""
echo "========================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "========================================"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}ALL CHECKS PASSED ✓${NC}"
    exit 0
else
    echo -e "${RED}SOME CHECKS FAILED${NC}"
    echo "View logs: journalctl -u evan-backend --no-pager -n 20"
    exit 1
fi
