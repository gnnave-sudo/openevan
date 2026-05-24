// evan.stresslab — CSL Stress Lab Skill for OpenClaw/QuickJS
// Calls OpenEvan v11 API at localhost:8001

const V11_API = env.V11_API || "http://localhost:8001";

async function simulate(args) {
  const res = await fetch(`${V11_API}/api/v1/stresslab/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: args.mode || "standard",
      matter_id: args.matter_id || null,
      context: args.context || "",
      product_class: args.product_class || null,
      jurisdiction: args.jurisdiction || null,
    }),
  });
  return res.json();
}

async function getResult(args) {
  const res = await fetch(`${V11_API}/api/v1/stresslab/result/${args.result_id}`);
  return res.json();
}

async function stats() {
  const res = await fetch(`${V11_API}/api/v1/stresslab/stats`);
  return res.json();
}

async function triggerForMatter(args) {
  const res = await fetch(`${V11_API}/api/v1/stresslab/trigger/${args.matter_id}?mode=${args.mode || "standard"}`, {
    method: "POST",
  });
  return res.json();
}

export default { simulate, getResult, stats, triggerForMatter };
