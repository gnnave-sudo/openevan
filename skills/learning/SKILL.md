# Continuous Learning

Track compliance posture scores over time, detect regulatory drift events, and maintain historical comparison baselines. Part of OpenEvan v11.

## When to Use

- Checking the organization's overall compliance health
- Detecting when regulatory changes impact your posture
- Comparing current posture to historical baselines
- Generating compliance trend reports for management

## Tools

### `posture`

Get the current compliance posture score.

```yaml
endpoint: http://localhost:8001/api/v1/learning/posture-score
method: GET
```

### `record_posture`

Calculate and record a new posture score from latest data.

```yaml
endpoint: http://localhost:8001/api/v1/learning/posture-score
method: POST
```

### `drift_timeline`

Get drift events over a time period.

```yaml
endpoint: http://localhost:8001/api/v1/learning/drift-timeline
method: GET
params:
  days: number   # default 90
```

### `detect_drift`

Trigger automated drift detection.

```yaml
endpoint: http://localhost:8001/api/v1/learning/drift-detect
method: POST
```

### `historical`

Get historical posture comparison.

```yaml
endpoint: http://localhost:8001/api/v1/learning/historical
method: GET
params:
  days: number   # default 180
```

## Posture Dimensions

- Regulatory Compliance (target: >75)
- Operational Risk (target: >65)
- Financial Stability (target: >70)
- Reputational Risk (target: >65)
- Technology Security (target: >70)

## Examples

```
Run learning posture
```

```
Run learning drift_timeline with days=30
```

```
Run learning detect_drift
```
