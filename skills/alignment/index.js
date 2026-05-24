// evan.alignment — Counsel Alignment Skill for OpenClaw/QuickJS

const V11_API = env.V11_API || "http://localhost:8001";

async function submitMemo(args) {
  const res = await fetch(`${V11_API}/api/v1/alignment/submit-memo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      counsel_name: args.counsel_name,
      memo_content: args.memo_content,
      jurisdiction: args.jurisdiction || null,
      product_area: args.product_area || null,
      matter_id: args.matter_id || null,
    }),
  });
  return res.json();
}

async function getResult(args) {
  const res = await fetch(`${V11_API}/api/v1/alignment/result/${args.result_id}`);
  return res.json();
}

async function forMatter(args) {
  const res = await fetch(`${V11_API}/api/v1/alignment/matter/${args.matter_id}`);
  return res.json();
}

export default { submitMemo, getResult, forMatter };
