# Stress Lab

Run 4-agent adversarial compliance stress simulations with 10-dimension weighted risk scoring. Integrates with the OpenEvan v11 analytical engine on port 8001.

## When to Use

- A new matter needs risk assessment before proceeding
- You need to simulate regulator, business, compliance, and adjudicator viewpoints
- You want a quantitative risk score across 10 weighted dimensions
- You need to identify control gaps and decisive obligations

## Tools

### `simulate`

Run a stress lab simulation for a matter or scenario.

```yaml
endpoint: http://localhost:8001/api/v1/stresslab/run
method: POST
body:
  mode: standard          # standard | adversarial | regulator_only | business_only | time_boxed | consensus | deep_dive
  matter_id: null         # optional — link to existing matter
  context: string         # scenario description (e.g., "Virtual Asset Exchange in Singapore")
  product_class: string   # e.g., "Virtual Asset Exchange", "Custody", "DeFi"
  jurisdiction: string    # e.g., "Singapore", "Hong Kong", "UK", "US"
```

Returns: overall_risk_score (0-100), final_recommendation (PROCEED/HOLD/NO-GO), 4 agent positions, 10 risk dimensions.

### `stats`

Get stress lab usage statistics.

```yaml
endpoint: http://localhost:8001/api/v1/stresslab/stats
method: GET
```

## Examples

**Quick risk check for a new product:**
```
Run stresslab simulate with mode=standard, context="DeFi lending protocol launch in Singapore", product_class="DeFi", jurisdiction="Singapore"
```

**Deep-dive on high-risk matter:**
```
Run stresslab simulate with mode=deep_dive, matter_id=<matter_id>, context="Cross-border custody expansion"
```

**Check historical simulation stats:**
```
Run stresslab stats
```

## Notes

- Risk score < 40: PROCEED (green)
- Risk score 40-70: HOLD (amber)
- Risk score > 70: NO-GO (red)
- Deep dive uses `deepseek-r1:32b`, others use `qwen3:8b`
- Results are persisted to SQLite and linked to matters
