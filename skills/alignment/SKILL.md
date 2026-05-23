# Counsel Alignment

Compare external counsel memos against internally derived positions across 5 dimensions. Identify gaps and generate recommendations. Part of OpenEvan v11.

## When to Use

- A new counsel memo arrives and you need to compare it to internal position
- Assessing whether counsel's advice aligns with the firm's risk appetite
- Identifying specific areas of disagreement with external advisors
- Generating questions for follow-up counsel calls

## Tools

### `submit_memo`

Submit a counsel memo for alignment analysis.

```yaml
endpoint: http://localhost:8001/api/v1/alignment/submit-memo
method: POST
body:
  counsel_name: string
  memo_content: string          # Full memo text
  jurisdiction: string          # optional
  product_area: string          # optional
  matter_id: string             # optional — link to existing matter
```

### `get_result`

Retrieve a previously analyzed alignment result.

```yaml
endpoint: http://localhost:8001/api/v1/alignment/result/{result_id}
method: GET
```

### `for_matter`

List all alignment analyses for a matter.

```yaml
endpoint: http://localhost:8001/api/v1/alignment/matter/{matter_id}
method: GET
```

### `stats`

Overall alignment statistics.

```yaml
endpoint: http://localhost:8001/api/v1/alignment/stats
method: GET
```

## 5 Dimensions

1. **Legal Interpretation** (25%) — Do we read the law the same way?
2. **Risk Assessment** (25%) — Is our risk evaluation aligned?
3. **Recommended Action** (20%) — Are our proposed actions compatible?
4. **Timeline** (15%) — Do we agree on timing?
5. **Jurisdictional Scope** (15%) — Is our territorial understanding aligned?

## Examples

```
Run alignment submit_memo with counsel_name="ABC Legal", memo_content="In our view, the MAS DPT license is not triggered by...", jurisdiction="Singapore", matter_id="matter-123"
```
