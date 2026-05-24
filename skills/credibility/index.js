// evan.credibility — Credibility Scorer Skill for OpenClaw/QuickJS

const V11_API = env.V11_API || "http://localhost:8001";

async function score(args) {
  const res = await fetch(`${V11_API}/api/v1/credibility/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      counsel_name: args.counsel_name,
      historical_accuracy: args.historical_accuracy,
      jurisdictional_depth: args.jurisdictional_depth,
      timeliness: args.timeliness,
      communication_clarity: args.communication_clarity,
      strategic_value: args.strategic_value,
      independence: args.independence,
      matter_id: args.matter_id || null,
    }),
  });
  return res.json();
}

async function leaderboard(args) {
  const q = new URLSearchParams();
  if (args.tier) q.set("tier", args.tier);
  q.set("limit", String(args.limit || 50));
  const res = await fetch(`${V11_API}/api/v1/credibility/leaderboard?${q}`);
  return res.json();
}

async function track(args) {
  const res = await fetch(`${V11_API}/api/v1/credibility/counsel/${encodeURIComponent(args.counsel_name)}`);
  return res.json();
}

async function stats() {
  const res = await fetch(`${V11_API}/api/v1/credibility/stats`);
  return res.json();
}

export default { score, leaderboard, track, stats };
