#!/bin/bash
# OpenEvan v12 Deploy Script — FIXED for gnnave user (no root needed)
set -e

# Use home directory instead of /opt
INSTALL_DIR="$HOME/openevan"
LOG="$HOME/openevan_deploy.log"
exec > >(tee -a "$LOG") 2>&1

echo "======================================"
echo "OpenEvan v12 Deploy — $(date)"
echo "User: $(whoami) | Home: $HOME"
echo "======================================"

# ── 1. Clone or Update ────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[1/7] Updating existing repo at $INSTALL_DIR..."
    cd "$INSTALL_DIR" && git pull origin main
else
    echo "[1/7] Cloning to $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/gnnave-sudo/openevan.git "$INSTALL_DIR"
fi

# ── 2. Install Deps ───────────────────────────────────────────────────────
echo "[2/7] Installing Python deps..."
pip3 install --user fastapi uvicorn pydantic aiosqlite httpx python-multipart -q 2>&1 | tail -3

# ── 3. Verify Import ──────────────────────────────────────────────────────
echo "[3/7] Verifying v11 merged API..."
cd "$INSTALL_DIR/merged"
python3 -c "
import sys
sys.path.insert(0, '.')
from app.main import app
paths = [r.path for r in app.routes if hasattr(r, 'path') and r.path]
print(f'OK: {len(set(paths))} unique paths loaded')
" 2>&1

# ── 4. Stop Existing ──────────────────────────────────────────────────────
echo "[4/7] Checking for existing server..."
pkill -f "uvicorn.*8001" 2>/dev/null || true
sleep 1

# ── 5. Start Server ───────────────────────────────────────────────────────
echo "[5/7] Starting v11 API on port 8001..."
cd "$INSTALL_DIR/merged"
export PYTHONPATH="$INSTALL_DIR/merged"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1 \
    > "$HOME/openevan_v11_server.log" 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for startup
for i in {1..15}; do
    sleep 1
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "[5/7] Server healthy on port 8001"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "[5/7] WARNING: Health check timed out"
        echo "--- Server log ---"
        tail -20 "$HOME/openevan_v11_server.log"
    fi
done

# ── 6. Install OpenClaw Skills ───────────────────────────────────────────
echo "[6/7] Installing OpenClaw skills..."
SKILL_DIR="$HOME/.openclaw/skills"
mkdir -p "$SKILL_DIR"

for skill in stresslab patterns credibility alignment learning intake; do
    mkdir -p "$SKILL_DIR/evan-$skill"
    if [ -f "$INSTALL_DIR/skills/$skill/SKILL.md" ]; then
        cp "$INSTALL_DIR/skills/$skill/SKILL.md" "$SKILL_DIR/evan-$skill/"
        echo "  Installed: evan-$skill"
    else
        echo "  Missing: $INSTALL_DIR/skills/$skill/SKILL.md"
    fi
done

# Integration bridge
mkdir -p "$SKILL_DIR/evan-integrations"
if [ -f "$INSTALL_DIR/skills/integrations/v11_client.js" ]; then
    cp "$INSTALL_DIR/skills/integrations/v11_client.js" "$SKILL_DIR/evan-integrations/"
    echo "  Installed: v11_client.js"
fi

echo "Skills installed at: $SKILL_DIR"
ls -la "$SKILL_DIR/" 2>/dev/null || echo "  (none yet)"

# ── 7. Load Neo4j Schema ─────────────────────────────────────────────────
echo "[7/7] Loading Neo4j graph schema..."
if docker ps | grep neo4j > /dev/null 2>&1; then
    echo "  Neo4j container running"
    if [ -f "$INSTALL_DIR/v12/graph/neo4j_legal_schema.cypher" ]; then
        # Use docker exec to run cypher inside the container
        docker exec neo4j cypher-shell -u neo4j -p openevan \
            --file /var/lib/neo4j/import/schema.cypher 2>/dev/null || \
        docker cp "$INSTALL_DIR/v12/graph/neo4j_legal_schema.cypher" neo4j:/tmp/schema.cypher 2>/dev/null && \
        docker exec neo4j bash -c "cat /tmp/schema.cypher | cypher-shell -u neo4j -p openevan" 2>/dev/null || \
        echo "  Neo4j schema load deferred — container may still be initializing"
    else
        echo "  Schema file not found at $INSTALL_DIR/v12/graph/neo4j_legal_schema.cypher"
    fi
else
    echo "  Neo4j not running — start with:"
    echo "  docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/openevan neo4j:5-community"
fi

# ── Summary ───────────────────────────────────────────────────────────────
echo ""
echo "======================================"
echo "DEPLOY COMPLETE"
echo "======================================"
echo "v11 API:       http://localhost:8001"
echo "Health:        curl http://localhost:8001/health"
echo "Docs:          curl http://localhost:8001/docs"
echo "Metrics:       curl http://localhost:8001/api/v1/metrics"
echo "Server log:    tail -f $HOME/openevan_v11_server.log"
echo "Deploy log:    tail -f $LOG"
echo "Install dir:   $INSTALL_DIR"
echo "Skills dir:    $SKILL_DIR"
echo ""
echo "--- Quick Test ---"
curl -s http://localhost:8001/health 2>/dev/null && echo "Health: OK" || echo "Health: PENDING"
echo ""
echo "Next: Restart your OpenHuman/OpenClaw gateway to pick up new skills"
echo "======================================"
