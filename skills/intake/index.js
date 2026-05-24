// evan.intake — Regulatory Intake Skill for OpenClaw/QuickJS

const V11_API = env.V11_API || "http://localhost:8001";

async function submit(args) {
  const res = await fetch(`${V11_API}/api/v1/intake/raw-input`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input_type: args.input_type || "regulatory_update",
      source: args.source,
      content: args.content,
    }),
  });
  return res.json();
}

async function factPacket(args) {
  const res = await fetch(`${V11_API}/api/v1/intake/fact-packet/${args.input_id}`);
  return res.json();
}

async function inputs(args) {
  const q = new URLSearchParams();
  if (args.status) q.set("status", args.status);
  q.set("limit", String(args.limit || 100));
  const res = await fetch(`${V11_API}/api/v1/intake/inputs?${q}`);
  return res.json();
}

async function packets(args) {
  const q = new URLSearchParams();
  if (args.jurisdiction) q.set("jurisdiction", args.jurisdiction);
  q.set("limit", String(args.limit || 100));
  const res = await fetch(`${V11_API}/api/v1/intake/packets?${q}`);
  return res.json();
}

export default { submit, factPacket, inputs, packets };
