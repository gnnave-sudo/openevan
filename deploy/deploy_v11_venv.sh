#!/bin/bash
# OpenEvan v12 Deploy — uses Python venv (no --break-system-packages needed)
set -e

INSTALL_DIR="$HOME/openevan"
VENV_DIR="$INSTALL_DIR/.venv"
LOG="$HOME/openevan_deploy.log"
exec > >(tee -a "$LOG") 2>&1

echo "======================================"
echo "OpenEvan v12 Deploy — $(date)"
echo "User: $(whoami) | Venv: $VENV_DIR"
echo "======================================"

# ── 1. Clone ──────────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[1/7] Updating $INSTALL_DIR..."
    cd "$INSTALL_DIR" && git pull origin main
else
    echo "[1/7] Cloning to $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/gnnave-sudo/openevan.git "$INSTALL_DIR"
fi

# ── 2. Create venv ────────────────────────────────────────────────────────
echo "[2/7] Creating Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# ── 3. Install deps inside venv ───────────────────────────────────────────
echo "[3/7] Installing dependencies into venv..."
pip install --upgrade pip -q
pip install fastapi uvicorn pydantic aiosqlite httpx python-multipart -q 2>&1 | tail -3

# ── 4. Verify import ──────────────────────────────────────────────────────
echo "[4/7] Verifying v11 merged API..."
cd "$INSTALL_DIR/merged"
python3 -c "
import sys
sys.path.insert(0, '.')
from app.main import app
paths = [r.path for r in app.routes if hasattr(r, 'path') and r.path]
print(f'OK: {len(set(paths))} unique paths loaded')
" 2>&1

# ── 5. Stop existing ──────────────────────────────────────────────────────
echo "[5/7] Stopping existing server..."
pkill -f "uvicorn.*8001" 2>/dev/null || true
sleep 1

# ── 6. Start server using venv Python ─────────────────────────────────────
echo "[6/7] Starting v11 API on port 8001..."
cd "$INSTALL_DIR/merged"
export PYTHONPATH="$INSTALL_DIR/merged"

# Use venv's Python explicitly
nohup "$VENV_DIR/bin/python" -m uvicorn app.main:app \
    --host 0.0.0.0 --port 8001 --workers 1 \
    > "$HOME/openevan_v11_server.log" 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for startup
for i in {1..15}; do
    sleep 1
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "[6/7] Server healthy on port 8001 (PID: $SERVER_PID)"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "[6/7] WARNING: Health check timed out"
        echo "--- Server log ---"
        tail -20 "$HOME/openevan_v11_server.log"
    fi
done

# ── 7. Install OpenClaw skills ────────────────────────────────────────────
echo "[7/7] Installing OpenClaw skills..."
SKILL_DIR="$HOME/.openclaw/skills"
mkdir -p "$SKILL_DIR"

for skill in stresslab patterns credibility alignment learning intake; do
    mkdir -p "$SKILL_DIR/evan-$skill"
    if [ -f "$INSTALL_DIR/skills/$skill/SKILL.md" ]; then
        cp "$INSTALL_DIR/skills/$skill/SKILL.md" "$SKILL_DIR/evan-$skill/"
        echo "  Installed: evan-$skill"
    fi
done

mkdir -p "$SKILL_DIR/evan-integrations"
cp "$INSTALL_DIR/skills/integrations/v11_client.js" "$SKILL_DIR/evan-integrations/" 2>/dev/null && echo "  Installed: v11_client.js"

# Neo4j schema
echo ""
echo "Neo4j schema load..."
if docker ps | grep neo4j > /dev/null 2>&1; then
    docker cp "$INSTALL_DIR/v12/graph/neo4j_legal_schema.cypher" neo4j:/tmp/ 2>/dev/null
    docker exec neo4j bash -c "cat /tmp/neo4j_legal_schema.cypher | cypher-shell -u neo4j -p openevan" 2>/dev/null && echo "  Schema loaded" || echo "  Schema deferred (container may be initializing)"
else
    echo "  Neo4j not running — docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/openevan neo4j:5-community"
fi

# ── Summary ───────────────────────────────────────────────────────────────
echo ""
echo "======================================"
echo "DEPLOY COMPLETE"
echo "======================================"
echo "v11 API:       http://localhost:8001"
echo "Health check:  curl http://localhost:8001/health"
echo "API docs:      curl http://localhost:8001/docs"
echo "Metrics:       curl http://localhost:8001/api/v1/metrics"
echo ""
echo "Logs:"
echo "  Server:      tail -f ~/openevan_v11_server.log"
echo "  Deploy:      tail -f ~/openevan_deploy.log"
echo ""
echo "Paths:"
echo "  Code:        ~/openevan/"
echo "  Venv:        ~/openevan/.venv/"
echo "  Skills:      ~/.openclaw/skills/"
echo ""
echo "Quick test:"
curl -s http://localhost:8001/health 2>/dev/null && echo "  Health: OK" || echo "  Health: still starting..."
echo ""
echo "Restart OpenClaw to pick up skills:"
echo "  pkill -f openclaw; sleep 1; (start openclaw)"
echo "======================================"
