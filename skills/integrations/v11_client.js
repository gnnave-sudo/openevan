/**
 * OpenEvan v11 API Client
 * Integration bridge for OpenClaw skills to call v11 analytical endpoints.
 * 
 * Usage in skill JS files:
 *   const v11 = require('./v11_client');
 *   const result = await v11.stresslab.simulate({ mode: 'standard', context: '...' });
 */

const V11_BASE = process.env.V11_API_URL || 'http://localhost:8001';

// ── Helpers ────────────────────────────────────────────────────────────────

async function v11fetch(path, opts = {}) {
  const url = `${V11_BASE}${path}`;
  const res = await fetch(url, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new Error(`v11 ${opts.method || 'GET'} ${path} → ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.status === 204 ? null : res.json();
}

// ── Stress Lab ─────────────────────────────────────────────────────────────

const stresslab = {
  async simulate({ mode = 'standard', matter_id = null, context = '', product_class = null, jurisdiction = null } = {}) {
    return v11fetch('/api/v1/stresslab/run', {
      method: 'POST',
      body: JSON.stringify({ mode, matter_id, context, product_class, jurisdiction }),
    });
  },
  async getResult(resultId) {
    return v11fetch(`/api/v1/stresslab/result/${resultId}`);
  },
  async stats() {
    return v11fetch('/api/v1/stresslab/stats');
  },
  async triggerForMatter(matterId, mode = 'standard') {
    return v11fetch(`/api/v1/stresslab/trigger/${matterId}?mode=${mode}`, { method: 'POST' });
  },
};

// ── Patterns ───────────────────────────────────────────────────────────────

const patterns = {
  async extract({ stress_result_id = null, matter_id = null } = {}) {
    return v11fetch('/api/v1/patterns/extract', {
      method: 'POST',
      body: JSON.stringify({ stress_result_id, matter_id }),
    });
  },
  async library({ matter_id = null, limit = 50 } = {}) {
    const q = matter_id ? `?matter_id=${matter_id}&limit=${limit}` : `?limit=${limit}`;
    return v11fetch(`/api/v1/patterns/library${q}`);
  },
  async riskIndex({ jurisdiction = null, product_class = null, time_range_days = 90 } = {}) {
    return v11fetch('/api/v1/patterns/risk-index', {
      method: 'POST',
      body: JSON.stringify({ jurisdiction, product_class, time_range_days }),
    });
  },
  async obligations({ matter_id = null } = {}) {
    const q = matter_id ? `?matter_id=${matter_id}` : '';
    return v11fetch(`/api/v1/patterns/obligations${q}`);
  },
};

// ── Credibility ────────────────────────────────────────────────────────────

const credibility = {
  async score({ counsel_name, historical_accuracy, jurisdictional_depth, timeliness, communication_clarity, strategic_value, independence, matter_id = null }) {
    return v11fetch('/api/v1/credibility/score', {
      method: 'POST',
      body: JSON.stringify({ counsel_name, historical_accuracy, jurisdictional_depth, timeliness, communication_clarity, strategic_value, independence, matter_id }),
    });
  },
  async leaderboard({ tier = null, limit = 50 } = {}) {
    const q = tier ? `?tier=${tier}&limit=${limit}` : `?limit=${limit}`;
    return v11fetch(`/api/v1/credibility/leaderboard${q}`);
  },
  async track(counselName) {
    return v11fetch(`/api/v1/credibility/counsel/${encodeURIComponent(counselName)}`);
  },
};

// ── Alignment ──────────────────────────────────────────────────────────────

const alignment = {
  async submitMemo({ counsel_name, memo_content, jurisdiction = null, product_area = null, matter_id = null }) {
    return v11fetch('/api/v1/alignment/submit-memo', {
      method: 'POST',
      body: JSON.stringify({ counsel_name, memo_content, jurisdiction, product_area, matter_id }),
    });
  },
  async forMatter(matterId) {
    return v11fetch(`/api/v1/alignment/matter/${matterId}`);
  },
};

// ── Learning ───────────────────────────────────────────────────────────────

const learning = {
  async posture() {
    return v11fetch('/api/v1/learning/posture-score');
  },
  async recordPosture() {
    return v11fetch('/api/v1/learning/posture-score', { method: 'POST' });
  },
  async driftTimeline({ days = 90 } = {}) {
    return v11fetch(`/api/v1/learning/drift-timeline?days=${days}`);
  },
  async detectDrift() {
    return v11fetch('/api/v1/learning/drift-detect', { method: 'POST' });
  },
};

// ── Intake ─────────────────────────────────────────────────────────────────

const intake = {
  async submit({ input_type = 'regulatory_update', source, content }) {
    return v11fetch('/api/v1/intake/raw-input', {
      method: 'POST',
      body: JSON.stringify({ input_type, source, content }),
    });
  },
  async factPacket(inputId) {
    return v11fetch(`/api/v1/intake/fact-packet/${inputId}`);
  },
  async inputs({ status = null, limit = 100 } = {}) {
    const q = status ? `?status=${status}&limit=${limit}` : `?limit=${limit}`;
    return v11fetch(`/api/v1/intake/inputs${q}`);
  },
};

// ── Matters (x870 integration) ─────────────────────────────────────────────

const matters = {
  async list({ status = null, jurisdiction = null, limit = 100 } = {}) {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (jurisdiction) params.set('jurisdiction', jurisdiction);
    params.set('limit', String(limit));
    return v11fetch(`/api/v1/matters?${params}`);
  },
  async get(matterId) {
    return v11fetch(`/api/v1/matters/${matterId}`);
  },
  async create(data) {
    return v11fetch('/api/v1/matters', { method: 'POST', body: JSON.stringify(data) });
  },
  async addEvent(matterId, event) {
    return v11fetch(`/api/v1/matters/${matterId}/events`, { method: 'POST', body: JSON.stringify(event) });
  },
};

// ── Health Check ───────────────────────────────────────────────────────────

async function health() {
  return v11fetch('/health');
}

async function metrics() {
  return v11fetch('/api/v1/metrics');
}

// ── Export ─────────────────────────────────────────────────────────────────

module.exports = {
  V11_BASE,
  stresslab,
  patterns,
  credibility,
  alignment,
  learning,
  intake,
  matters,
  health,
  metrics,
};
