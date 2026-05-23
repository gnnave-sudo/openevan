#!/bin/bash
# Evan Legal Quant Stack — Full Cleanup + Persistence Setup
# Run as root on gnnave-x870.tail8e40c8.ts.net

set -e
VENV=/opt/evan-legal-quant/venv
BACKEND=/opt/evan-legal-quant/backend
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
pass() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }

echo "=========================================="
echo "  Evan Legal Quant Stack — Cleanup"
echo "=========================================="

# ============================================================
# 1. KILL ALL STALE PROCESSES
# ============================================================
log "Step 1: Killing stale processes..."

# Kill old compliance-stress-lab processes
pkill -f "compliance-stress-lab" 2>/dev/null || true
pkill -f "csl-engine" 2>/dev/null || true
pkill -f "csl_web" 2>/dev/null || true
pkill -f "csl-web" 2>/dev/null || true

# Kill any Python serving on port 8000 or 11434
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 11434/tcp 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true

sleep 2
pass "Stale processes killed"

# ============================================================
# 2. REMOVE OLD / COMPETING CODEBASE
# ============================================================
log "Step 2: Removing old compliance-stress-lab..."

if [ -d "/opt/compliance-stress-lab" ]; then
    rm -rf /opt/compliance-stress-lab
    pass "Removed /opt/compliance-stress-lab (old competing codebase)"
else
    warn "No old compliance-stress-lab found"
fi

# Remove stale Docker containers for old CSL
docker ps -a --filter "name=csl" --format "{{.ID}}" 2>/dev/null | while read cid; do
    docker rm -f "$cid" 2>/dev/null || true
    pass "Removed old Docker container: $cid"
done

# ============================================================
# 3. CLEAN STALE FILES IN NEW CODEBASE
# ============================================================
log "Step 3: Cleaning stale files..."

# Remove __pycache__ everywhere
find /opt/evan-legal-quant -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /opt/evan-legal-quant -name "*.pyc" -delete 2>/dev/null || true
pass "Removed __pycache__ and .pyc files"

# Remove stale/corrupted database
if [ -f "$BACKEND/evan_legal_quant.db" ]; then
    rm -f "$BACKEND/evan_legal_quant.db"
    pass "Removed stale database"
fi

# Remove old log files
rm -f /tmp/ollama.log /tmp/backend*.log /tmp/b*.log /tmp/o*.log 2>/dev/null || true
pass "Cleaned temp logs"

# Remove stale startup scripts
rm -f /opt/evan-legal-quant/start.sh /opt/evan-legal-quant/test_imports.py 2>/dev/null || true

# ============================================================
# 4. VERIFY VIRTUALENV & DEPS
# ============================================================
log "Step 4: Verifying virtualenv..."

if [ ! -d "$VENV" ]; then
    warn "Virtualenv not found, creating..."
    python3 -m venv "$VENV"
    $VENV/bin/pip install -r "$BACKEND/requirements.txt"
    pass "Created virtualenv + installed deps"
else
    pass "Virtualenv exists"
fi

# Quick import test
$VENV/bin/python -c "import fastapi, pydantic, uvicorn, aiosqlite, httpx; print('ALL_DEPS_OK')" 2>&1 | grep -q "ALL_DEPS_OK" && pass "All Python dependencies OK" || fail "Missing dependencies"

# ============================================================
# 5. CREATE SYSTEMD SERVICES
# ============================================================
log "Step 5: Creating systemd services..."

cat > /etc/systemd/system/evan-ollama.service << 'EOF'
[Unit]
Description=Evan Legal Quant — Mock Ollama LLM Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/evan-legal-quant
ExecStart=/opt/evan-legal-quant/venv/bin/python /opt/evan-legal-quant/mock_ollama_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=evan-ollama

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/evan-backend.service << 'EOF'
[Unit]
Description=Evan Legal Quant — Backend API (8 layers + Credibility)
After=network.target evan-ollama.service
Requires=evan-ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/evan-legal-quant/backend
Environment="OLLAMA_HOST=http://localhost:11434"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/evan-legal-quant/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=evan-backend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable evan-ollama evan-backend
pass "Systemd services created and enabled"

# ============================================================
# 6. START SERVICES
# ============================================================
log "Step 6: Starting services..."

systemctl stop evan-ollama 2>/dev/null || true
systemctl stop evan-backend 2>/dev/null || true
sleep 1
systemctl start evan-ollama
sleep 2
systemctl start evan-backend
sleep 3

# Verify
OLLAMA_STATUS=$(curl -s http://localhost:11434/api/tags 2>&1 | head -c 50)
BACKEND_STATUS=$(curl -s http://localhost:8000/ 2>&1 | head -c 100)

echo "$OLLAMA_STATUS" | grep -q "llama3.2" && pass "Mock Ollama running on :11434" || warn "Ollama may need more time"
echo "$BACKEND_STATUS" | grep -q "operational" && pass "Backend API running on :8000" || warn "Backend may need more time"

# ============================================================
# 7. RUN E2E TEST
# ============================================================
log "Step 7: Running E2E test..."

cd /opt/evan-legal-quant
$VENV/bin/python e2e_test.py 2>&1 | tail -40

# ============================================================
# 8. FINAL STATUS
# ============================================================
echo ""
echo "=========================================="
echo "  DEPLOYMENT STATUS"
echo "=========================================="

systemctl status evan-ollama --no-pager 2>&1 | head -5
echo "---"
systemctl status evan-backend --no-pager 2>&1 | head -5

echo ""
echo "Services:"
echo "  Backend API:    http://$(hostname -I | awk '{print $1}'):8000"
echo "  Mock Ollama:    http://localhost:11434"
echo "  Health check:   curl http://localhost:8000/"
echo "  Logs:           journalctl -u evan-backend -f"
echo "                  journalctl -u evan-ollama -f"
echo ""
echo "Commands:"
echo "  Restart:        systemctl restart evan-backend evan-ollama"
echo "  Stop:           systemctl stop evan-backend evan-ollama"
echo "  Status:         systemctl status evan-backend evan-ollama"
echo "  E2E test:       cd /opt/evan-legal-quant && venv/bin/python e2e_test.py"
echo ""
