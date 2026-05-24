// evan.learning — Continuous Learning Skill for OpenClaw/QuickJS

const V11_API = env.V11_API || "http://localhost:8001";

async function posture() {
  const res = await fetch(`${V11_API}/api/v1/learning/posture-score`);
  return res.json();
}

async function recordPosture() {
  const res = await fetch(`${V11_API}/api/v1/learning/posture-score`, { method: "POST" });
  return res.json();
}

async function driftTimeline(args) {
  const days = args.days || 90;
  const res = await fetch(`${V11_API}/api/v1/learning/drift-timeline?days=${days}`);
  return res.json();
}

async function detectDrift() {
  const res = await fetch(`${V11_API}/api/v1/learning/drift-detect`, { method: "POST" });
  return res.json();
}

async function historical(args) {
  const days = args.days || 180;
  const res = await fetch(`${V11_API}/api/v1/learning/historical?days=${days}`);
  return res.json();
}

export default { posture, recordPosture, driftTimeline, detectDrift, historical };
