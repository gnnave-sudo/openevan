#!/bin/bash
# Install ALL 12 Evan skills (6 existing + 6 new analytical) with OpenClaw registration
set -e

REPO="https://raw.githubusercontent.com/gnnave-sudo/openevan/main"
SKILL_DIR="/root/.openclaw/skills"
CONFIG="/root/.openclaw/openclaw.json"

echo "======================================"
echo "Installing 12 Evan Skills + Registration"
echo "User: $(whoami) | Dir: $SKILL_DIR"
echo "======================================"

# ── 1. Ensure skill directories exist ─────────────────────────────────────
mkdir -p "$SKILL_DIR"

# ── 2. Download 6 NEW analytical skills (QuickJS runtime + SKILL.md) ──────
echo "[1/3] Downloading 6 analytical skills..."
for skill in stresslab patterns credibility alignment learning intake; do
    mkdir -p "$SKILL_DIR/evan-$skill"
    curl -fsSL "$REPO/skills/$skill/index.js" > "$SKILL_DIR/evan-$skill/index.js" && \
        echo "  OK: evan-$skill/index.js" || echo "  FAIL: evan-$skill/index.js"
    # Also ensure SKILL.md exists
    if [ ! -f "$SKILL_DIR/evan-$skill/SKILL.md" ]; then
        curl -fsSL "$REPO/skills/$skill/SKILL.md" > "$SKILL_DIR/evan-$skill/SKILL.md" 2>/dev/null || true
    fi
done

# Integration bridge
mkdir -p "$SKILL_DIR/evan-integrations"
curl -fsSL "$REPO/skills/integrations/v11_client.js" > "$SKILL_DIR/evan-integrations/v11_client.js" && \
    echo "  OK: v11_client.js" || echo "  FAIL: v11_client.js"

# ── 3. Register in openclaw.json ─────────────────────────────────────────
echo "[2/3] Registering skills with OpenClaw..."

if [ -f "$CONFIG" ]; then
    # Backup existing config
    cp "$CONFIG" "$CONFIG.backup.$(date +%s)"
    
    # Download registration snippet
    curl -fsSL "$REPO/config/openclaw_skill_registration.json" > /tmp/openclaw_registration.json
    
    # Merge: if skills.entries exists, append; else create
    python3 << 'PYEOF'
import json, sys

config_path = "/root/.openclaw/openclaw.json"
reg_path = "/tmp/openclaw_registration.json"

try:
    with open(config_path) as f:
        config = json.load(f)
except:
    config = {}

with open(reg_path) as f:
    registration = json.load(f)

new_entries = registration.get("skills", {}).get("entries", [])

# Get existing entries
existing = config.get("skills", {}).get("entries", [])
existing_ids = {e.get("id") for e in existing}

# Add only new entries
added = 0
for entry in new_entries:
    if entry.get("id") not in existing_ids:
        existing.append(entry)
        added += 1

if "skills" not in config:
    config["skills"] = {}
config["skills"]["entries"] = existing

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"  Registered {added} new skills (skipped {len(new_entries) - added} existing)")
PYEOF
else
    # No existing config — create fresh
    echo "  Creating fresh openclaw.json..."
    curl -fsSL "$REPO/config/openclaw_skill_registration.json" > "$CONFIG"
    echo "  Created: $CONFIG"
fi

# ── 4. Verify ─────────────────────────────────────────────────────────────
echo "[3/3] Verification..."
echo ""
echo "Skill directories:"
ls -d "$SKILL_DIR"/evan-* 2>/dev/null | while read d; do
    name=$(basename "$d")
    files=$(ls "$d" 2>/dev/null | wc -l)
    echo "  $name ($files files)"
done

echo ""
echo "Registered skills in openclaw.json:"
python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
entries = c.get('skills', {}).get('entries', [])
evan = [e for e in entries if e.get('id', '').startswith('evan.')]
for e in evan:
    status = 'enabled' if e.get('enabled') else 'disabled'
    print(f'  {e[\"id\"]} ({status})')
print(f'Total evan skills: {len(evan)}')
" 2>/dev/null || echo "  (could not parse config)"

echo ""
echo "======================================"
echo "INSTALL COMPLETE"
echo "======================================"
echo "Skills: $SKILL_DIR/evan-*/"
echo "Config: $CONFIG"
echo ""
echo "Next: Restart OpenClaw to pick up new skills"
echo "  pkill -9 -f openclaw; sleep 2; (start openclaw)"
echo "======================================"
