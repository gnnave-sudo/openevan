#!/bin/bash
# Install OpenClaw skills for v12
# Works for both root and gnnave users

REPO="https://raw.githubusercontent.com/gnnave-sudo/openevan/main"

# Detect user - install to correct path
if [ "$(whoami)" = "root" ]; then
    SKILL_DIR="/root/.openclaw/skills"
else
    SKILL_DIR="$HOME/.openclaw/skills"
fi

echo "Installing OpenClaw skills for user: $(whoami)"
echo "Skill directory: $SKILL_DIR"
mkdir -p "$SKILL_DIR"

# 6 v11 analytical skills
for skill in stresslab patterns credibility alignment learning intake; do
    mkdir -p "$SKILL_DIR/evan-$skill"
    echo "  Downloading evan-$skill/SKILL.md..."
    curl -fsSL "$REPO/skills/$skill/SKILL.md" > "$SKILL_DIR/evan-$skill/SKILL.md" && \
        echo "    OK: evan-$skill" || \
        echo "    FAIL: evan-$skill"
done

# Integration bridge
mkdir -p "$SKILL_DIR/evan-integrations"
echo "  Downloading v11_client.js..."
curl -fsSL "$REPO/skills/integrations/v11_client.js" > "$SKILL_DIR/evan-integrations/v11_client.js" && \
    echo "    OK: v11_client.js" || \
    echo "    FAIL: v11_client.js"

echo ""
echo "Skills installed at: $SKILL_DIR"
echo "Contents:"
find "$SKILL_DIR" -type f -exec ls -la {} \;

echo ""
echo "Next: Restart OpenClaw gateway to pick up new skills"
