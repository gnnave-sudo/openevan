# Pattern Extractor

Extract recurring regulatory obligations, risk drivers, compliance weaknesses, and early warning signals from stress lab results and matters. Part of the OpenEvan v11 analytical engine.

## When to Use

- After a stress lab run to extract actionable patterns
- Building a library of recurring obligations across matters
- Querying risk indices by jurisdiction or product class
- Identifying compliance weaknesses across the portfolio

## Tools

### `extract`

Extract patterns from a stress lab result or matter.

```yaml
endpoint: http://localhost:8001/api/v1/patterns/extract
method: POST
body:
  stress_result_id: string   # optional — extract from specific stress result
  matter_id: string          # optional — extract from matter's latest stress result
```

### `library`

Browse the pattern library.

```yaml
endpoint: http://localhost:8001/api/v1/patterns/library
method: GET
params:
  matter_id: string   # optional — filter by matter
  limit: number       # default 50
```

### `risk_index`

Query aggregated risk indices.

```yaml
endpoint: http://localhost:8001/api/v1/patterns/risk-index
method: POST
body:
  jurisdiction: string     # optional — filter by jurisdiction
  product_class: string    # optional — filter by product
  time_range_days: number  # default 90
```

### `obligations`

List all recurring obligations.

```yaml
endpoint: http://localhost:8001/api/v1/patterns/obligations
method: GET
params:
  matter_id: string   # optional
```

## Examples

**Extract patterns after stress lab:**
```
Run patterns extract with stress_result_id=<result_id>
```

**Get risk index for Singapore:**
```
Run patterns risk_index with jurisdiction="Singapore", time_range_days=90
```

**List recurring obligations:**
```
Run patterns obligations
```
