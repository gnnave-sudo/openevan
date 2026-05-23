# Regulatory Intake

Submit raw regulatory text and automatically extract structured FactPackets with jurisdiction, obligations, controls, and risk signals. Part of OpenEvan v11.

## When to Use

- A new regulatory circular, enforcement action, or consultation paper arrives
- You need to quickly understand what a regulatory document requires
- Building a structured regulatory database from unstructured inputs
- Feeding regulatory updates into the stress lab or matter system

## Tools

### `submit`

Submit raw regulatory text for processing.

```yaml
endpoint: http://localhost:8001/api/v1/intake/raw-input
method: POST
body:
  input_type: string   # regulatory_update | enforcement_action | news | internal_memo
  source: string       # e.g., "MAS Circular PSN02", "SEC Enforcement"
  content: string      # Full text of the regulatory document
```

### `fact_packet`

Get the extracted FactPacket for a raw input.

```yaml
endpoint: http://localhost:8001/api/v1/intake/fact-packet/{input_id}
method: GET
```

### `inputs`

List all processed raw inputs.

```yaml
endpoint: http://localhost:8001/api/v1/intake/inputs
method: GET
params:
  status: string    # pending | processed
  limit: number     # default 100
```

### `packets`

List all extracted FactPackets.

```yaml
endpoint: http://localhost:8001/api/v1/intake/packets
method: GET
params:
  jurisdiction: string   # optional filter
  limit: number          # default 100
```

## FactPacket Fields

- **Jurisdiction** — Auto-detected (Singapore, HK, UK, US, EU, etc.)
- **Regulator** — MAS, SFC, FCA, SEC, ESMA, etc.
- **Product Class** — VASP, Exchange, Custody, DeFi, etc.
- **Obligations** — Structured list of compliance requirements
- **Controls** — Required control measures
- **Risk Signals** — Early warning indicators

## Examples

```
Run intake submit with input_type="regulatory_update", source="MAS Circular PSN02", content="The Monetary Authority of Singapore today issued updated guidance on Digital Payment Token services..."
```
