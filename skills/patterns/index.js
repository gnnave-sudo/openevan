// evan.patterns — Pattern Extractor Skill for OpenClaw/QuickJS

const V11_API = env.V11_API || "http://localhost:8001";

async function extract(args) {
  const res = await fetch(`${V11_API}/api/v1/patterns/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      stress_result_id: args.stress_result_id || null,
      matter_id: args.matter_id || null,
    }),
  });
  return res.json();
}

async function library(args) {
  const q = new URLSearchParams();
  if (args.matter_id) q.set("matter_id", args.matter_id);
  q.set("limit", String(args.limit || 50));
  const res = await fetch(`${V11_API}/api/v1/patterns/library?${q}`);
  return res.json();
}

async function riskIndex(args) {
  const res = await fetch(`${V11_API}/api/v1/patterns/risk-index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jurisdiction: args.jurisdiction || null,
      product_class: args.product_class || null,
      time_range_days: args.time_range_days || 90,
    }),
  });
  return res.json();
}

async function obligations(args) {
  const q = args.matter_id ? `?matter_id=${args.matter_id}` : "";
  const res = await fetch(`${V11_API}/api/v1/patterns/obligations${q}`);
  return res.json();
}

export default { extract, library, riskIndex, obligations };
