#!/bin/bash
# OpenEvan v11 Deploy Script for x870
# Run this on gnnave-x870:  bash <(curl -fsSL https://raw.githubusercontent.com/gnnave-sudo/openevan/main/deploy/deploy_v11.sh)
set -e

LOG="/tmp/openevan_v11_deploy.log"
exec > >(tee -a "$LOG") 2>&1

echo "======================================"
echo "OpenEvan v11 Deploy — $(date)"
echo "======================================"

cd /tmp

# Clone or update
if [ -d "/opt/openevan/.git" ]; then
    echo "[1/6] Updating existing repo..."
    cd /opt/openevan && git pull origin main
else
    echo "[1/6] Cloning openevan repo..."
    rm -rf /opt/openevan
    git clone https://github.com/gnnave-sudo/openevan.git /opt/openevan
fi

echo "[2/6] Installing Python deps..."
pip3 install fastapi uvicorn pydantic aiosqlite httpx python-multipart -q 2>&1 | tail -3

echo "[3/6] Verifying v11 merged API..."
cd /opt/openevan/merged
python3 -c "
import sys
sys.path.insert(0, '.')
from app.main import app
paths = [r.path for r in app.routes if hasattr(r, 'path') and r.path]
print(f'OK: {len(set(paths))} unique paths')
print(f'OK: {len([r for r in app.routes if hasattr(r, \"methods\") and r.methods])} endpoints')
"

echo "[4/6] Stopping any existing v11 server..."
kill $(lsof -t -i:8001) 2>/dev/null || true
sleep 1

echo "[5/6] Starting v11 unified API on port 8001..."
cd /opt/openevan/merged
export PYTHONPATH=/opt/openevan/merged
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1 > /tmp/openevan_v11_server.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for startup
for i in {1..10}; do
    sleep 1
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "[6/6] Server healthy on port 8001"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "[6/6] WARNING: Server health check timed out, checking logs..."
        tail -20 /tmp/openevan_v11_server.log
    fi
done

echo ""
echo "======================================"
echo "DEPLOY COMPLETE"
echo "======================================"
echo "v11 API:       http://localhost:8001"
echo "Health:        curl http://localhost:8001/health"
echo "Docs:          curl http://localhost:8001/docs"
echo "Metrics:       curl http://localhost:8001/api/v1/metrics"
echo "Process:       ps aux | grep uvicorn | grep 8001"
echo "Server log:    tail -f /tmp/openevan_v11_server.log"
echo "Deploy log:    tail -f $LOG"
echo "======================================"

# Quick smoke test
echo ""
echo "--- Smoke Test ---"
curl -s http://localhost:8001/health 2>/dev/null | head -1 || echo "Health endpoint not yet ready"
curl -s http://localhost:8001/api/v1/metrics 2>/dev/null | head -1 || echo "Metrics not yet ready"
curl -s -X POST http://localhost:8001/api/v1/stresslab/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"standard","context":"Virtual Asset Exchange in Singapore"}' 2>/dev/null | head -1 || echo "Stresslab not yet ready"

echo ""
echo "Add skills:    cp /opt/openevan/skills/*/SKILL.md /root/.openclaw/skills/"
echo "Then restart:  systemctl --user restart openclaw-gateway"
