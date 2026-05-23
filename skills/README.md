# OpenEvan v11 — OpenClaw Skills & Integrations

This directory contains OpenClaw skill manifests and JS integration files for the OpenEvan v11 analytical engine.

## Structure

```
skills/
├── stresslab/SKILL.md         # CSL Stress Lab skill manifest
├── patterns/SKILL.md          # Pattern Extractor skill manifest
├── credibility/SKILL.md       # Credibility Scorer skill manifest
├── alignment/SKILL.md         # Counsel Alignment skill manifest
├── learning/SKILL.md          # Continuous Learning skill manifest
├── intake/SKILL.md            # Regulatory Intake skill manifest
├── integrations/
│   ├── v11_client.js          # JS API client for v11 endpoints
│   ├── contract_sim_enhanced.js   # Enhanced contract_sim with CSL
│   └── redline_agent_enhanced.js  # Enhanced redline_agent with CSL
└── README.md
```

## Quick Deploy to x870

```bash
# 1. Start v11 API (port 8001)
curl -fsSL https://raw.githubusercontent.com/gnnave-sudo/openevan/main/deploy/deploy_v11.sh | bash

# 2. Install OpenClaw skills
sudo bash -c '
  REPO="https://raw.githubusercontent.com/gnnave-sudo/openevan/main"
  for skill in stresslab patterns credibility alignment learning intake; do
    mkdir -p /root/.openclaw/skills/evan-$skill
    curl -fsSL "$REPO/skills/$skill/SKILL.md" > /root/.openclaw/skills/evan-$skill/SKILL.md
  done
  mkdir -p /root/.openclaw/skills/evan-integrations
  curl -fsSL "$REPO/skills/integrations/v11_client.js" > /root/.openclaw/skills/evan-integrations/v11_client.js
'

# 3. Restart OpenClaw
systemctl --user restart openclaw-gateway

# 4. Verify
/skills  # Should show evan-* skills
```

## v11 API Endpoints

| Domain | Endpoints | Port |
|--------|----------|------|
| x870 Evan-AI (base) | 62 | 8000 |
| **OpenEvan v11 (merged)** | **98** | **8001** |

## Skill Integration

The `v11_client.js` module provides a JS client for all v11 endpoints:

```javascript
const v11 = require('./v11_client');

// Run stress lab
const result = await v11.stresslab.simulate({
  mode: 'standard',
  context: 'DeFi lending protocol in Singapore',
  product_class: 'DeFi',
  jurisdiction: 'Singapore',
});

// Score counsel
const score = await v11.credibility.score({
  counsel_name: 'ABC Legal',
  historical_accuracy: 92,
  jurisdictional_depth: 85,
  timeliness: 78,
  communication_clarity: 88,
  strategic_value: 80,
  independence: 75,
});

// Check posture
const posture = await v11.learning.posture();
```
