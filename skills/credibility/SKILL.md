# Credibility Scorer

Score external counsel on 6 dimensions with automatic tier classification. Track historical performance and rank counsel by effectiveness. Part of OpenEvan v11.

## When to Use

- Evaluating a new external counsel before engagement
- Tracking counsel performance over time
- Comparing multiple counsel for a matter
- Building a counsel leaderboard for the organization

## Tools

### `score`

Score counsel on 6 dimensions (0-100 each, auto-detects 0-1 scale).

```yaml
endpoint: http://localhost:8001/api/v1/credibility/score
method: POST
body:
  counsel_name: string
  historical_accuracy: number      # 0-100 (or 0-1, auto-detected)
  jurisdictional_depth: number     # 0-100
  timeliness: number               # 0-100
  communication_clarity: number    # 0-100
  strategic_value: number          # 0-100
  independence: number             # 0-100
  matter_id: string                # optional — link to matter
```

### `leaderboard`

Ranked table of all scored counsel.

```yaml
endpoint: http://localhost:8001/api/v1/credibility/leaderboard
method: GET
params:
  tier: string   # Elite | Established | Developing | Monitor
  limit: number  # default 50
```

### `track`

Get historical scores and trend for a counsel.

```yaml
endpoint: http://localhost:8001/api/v1/credibility/counsel/{counsel_name}
method: GET
```

### `stats`

Overall credibility statistics.

```yaml
endpoint: http://localhost:8001/api/v1/credibility/stats
method: GET
```

## Tier Classification

- **Elite** (≥85): Top-tier, reliable across all dimensions
- **Established** (70-84): Solid performer with minor gaps
- **Developing** (50-69): Potential but needs monitoring
- **Monitor** (<50): Significant concerns, require oversight

## Examples

```
Run credibility score with counsel_name="ABC Legal", historical_accuracy=92, jurisdictional_depth=85, timeliness=78, communication_clarity=88, strategic_value=80, independence=75
```

```
Run credibility leaderboard with limit=10
```
