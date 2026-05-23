/**
 * redline_agent v11-enhanced
 * Redlines legal documents using CSL stress lab for risk context.
 * Integrates with OpenEvan v11 analytical engine.
 * 
 * Usage: node redline_agent_enhanced.js --doc <file> [--jurisdiction <j>] [--matter <id>]
 */

const fs = require('fs');
const path = require('path');

const V11_BASE = process.env.V11_API_URL || 'http://localhost:8001';

async function v11fetch(path, body) {
  try {
    const res = await fetch(`${V11_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
}

async function redlineDocument(docPath, jurisdiction = 'Global', matterId = null) {
  console.error(`[redline] Analyzing ${docPath}...`);
  const content = fs.readFileSync(docPath, 'utf-8');
  
  // Step 1: Identify risky clauses
  const redlines = identifyRedlines(content);
  console.error(`[redline] Found ${redlines.length} items requiring attention`);
  
  // Step 2: Get stress lab context
  console.error('[redline] Getting CSL risk context...');
  const stressResult = await v11fetch('/api/v1/stresslab/run', {
    mode: 'regulator_only',
    context: `Redline review of ${path.basename(docPath)}: ${redlines.slice(0, 3).map(r => r.category).join(', ')}`,
    jurisdiction,
    matter_id: matterId,
  });
  
  // Step 3: Get alignment if matter exists
  let alignmentData = null;
  if (matterId) {
    try {
      const alignRes = await fetch(`${V11_BASE}/api/v1/alignment/matter/${matterId}`);
      if (alignRes.ok) alignmentData = await alignRes.json();
    } catch { /* ignore */ }
  }
  
  // Step 4: Get current posture
  let posture = null;
  try {
    const posRes = await fetch(`${V11_BASE}/api/v1/learning/posture-score`);
    if (posRes.ok) posture = await posRes.json();
  } catch { /* ignore */ }
  
  // Build output
  const output = {
    document: path.basename(docPath),
    jurisdiction,
    matter_id: matterId,
    redlines: redlines.map(r => ({
      ...r,
      suggested_language: suggestFix(r.category, r.original),
    })),
    risk_context: stressResult ? {
      overall_risk_score: stressResult.overall_risk_score,
      recommendation: stressResult.final_recommendation,
      regulator_objections: stressResult.regulator_objections || [],
      control_gaps: stressResult.key_control_gaps || [],
    } : null,
    alignment_context: alignmentData,
    current_posture: posture,
    summary: generateSummary(redlines, stressResult),
    generated_at: new Date().toISOString(),
  };
  
  return output;
}

function identifyRedlines(text) {
  const checks = [
    {
      category: 'unlimited_indemnity',
      pattern: /indemnify.*unlimited|unlimited.*indemnif|indemnif.*all claims/gi,
      severity: 'critical',
      reason: 'Unlimited indemnity creates unquantifiable liability exposure',
    },
    {
      category: 'broad_termination',
      pattern: /terminat.*for convenience|terminat.*at any time|terminat.*without cause/gi,
      severity: 'high',
      reason: 'Termination for convenience without notice period creates operational risk',
    },
    {
      category: 'weak_liability_cap',
      pattern: /liability.*cap.*\$\d{1,3},?\d{0,3}|liability.*limited.*amount/gi,
      severity: 'medium',
      reason: 'Verify liability cap is appropriate for transaction size and risk profile',
    },
    {
      category: 'missing_aml_clause',
      pattern: /aml|anti.money laundering|kyc|know your customer/gi,
      severity: 'high',
      reason: 'AML/KYC clause absent — may be required for regulated activities',
      inverse: true, // flag if NOT found
    },
    {
      category: 'data_residency',
      pattern: /data.*store.*outside|transfer.*data.*outside|cross.border.*data/gi,
      severity: 'medium',
      reason: 'Data residency/transfers may trigger PDPA/GDPR requirements',
    },
    {
      category: 'ip_assignment',
      pattern: /assign.*all.*intellectual property|ip.*transfer.*ownership/gi,
      severity: 'high',
      reason: 'Broad IP assignment may conflict with existing licensing arrangements',
    },
    {
      category: 'auto_renewal',
      pattern: /automatic.*renew|auto.renew|renew.*unless.*terminat/gi,
      severity: 'low',
      reason: 'Auto-renewal without adequate notice period for cancellation',
    },
    {
      category: 'governing_law_risk',
      pattern: /governed by.*laws of (?!Singapore|England|New York)/gi,
      severity: 'medium',
      reason: 'Unfamiliar governing law jurisdiction may increase enforcement difficulty',
    },
  ];
  
  const found = [];
  for (const check of checks) {
    const matches = text.match(check.pattern);
    const hasMatch = matches && matches.length > 0;
    
    if (check.inverse ? !hasMatch : hasMatch) {
      const idx = check.inverse ? 0 : text.search(check.pattern);
      found.push({
        category: check.category,
        severity: check.severity,
        reason: check.reason,
        original: check.inverse 
          ? '[CLAUSE ABSENT — should be added]' 
          : text.slice(Math.max(0, idx - 40), idx + 100).replace(/\s+/g, ' ').trim(),
        occurrences: check.inverse ? 0 : matches.length,
      });
    }
  }
  
  return found.sort((a, b) => {
    const sev = { critical: 4, high: 3, medium: 2, low: 1 };
    return sev[b.severity] - sev[a.severity];
  });
}

function suggestFix(category, original) {
  const fixes = {
    unlimited_indemnity: 'Cap indemnity at [12/18/24] months of fees or S$[amount], exclude consequential damages',
    broad_termination: 'Add [30/60/90]-day termination notice requirement with transition assistance clause',
    weak_liability_cap: 'Confirm liability cap equals 12 months of contract value or S$[appropriate amount]',
    missing_aml_clause: 'Insert: "Each party shall comply with applicable AML/CFT laws including MAS Notice PSN02"',
    data_residency: 'Add: "Personal data shall be stored in [Singapore/approved jurisdiction] unless explicitly consented"',
    ip_assignment: 'Limit IP assignment to project deliverables only; exclude background IP and pre-existing materials',
    auto_renewal: 'Add: "Either party may cancel auto-renewal with [30/60]-day written notice before term end"',
    governing_law_risk: 'Confirm internal legal has reviewed enforceability in chosen jurisdiction',
  };
  return fixes[category] || 'Review with legal counsel';
}

function generateSummary(redlines, stressResult) {
  const critical = redlines.filter(r => r.severity === 'critical').length;
  const high = redlines.filter(r => r.severity === 'high').length;
  const medium = redlines.filter(r => r.severity === 'medium').length;
  
  let summary = `${redlines.length} redlines: ${critical} critical, ${high} high, ${medium} medium.`;
  
  if (stressResult) {
    summary += ` CSL risk score: ${stressResult.overall_risk_score}/100 (${stressResult.final_recommendation}).`;
  }
  
  if (critical > 0) {
    summary += ' DO NOT SIGN without addressing critical items.';
  } else if (high > 2) {
    summary += ' Elevated risk — escalate to GC before proceeding.';
  }
  
  return summary;
}

// CLI
async function main() {
  const args = process.argv.slice(2);
  const docIdx = args.indexOf('--doc');
  const jurisIdx = args.indexOf('--jurisdiction');
  const matterIdx = args.indexOf('--matter');
  
  if (docIdx === -1 || !args[docIdx + 1]) {
    console.error('Usage: node redline_agent_enhanced.js --doc <file> [--jurisdiction <j>] [--matter <id>]');
    process.exit(1);
  }
  
  const result = await redlineDocument(
    args[docIdx + 1],
    jurisIdx !== -1 ? args[jurisIdx + 1] : 'Global',
    matterIdx !== -1 ? args[matterIdx + 1] : null,
  );
  console.log(JSON.stringify(result, null, 2));
}

if (require.main === module) {
  main();
}

module.exports = { redlineDocument, identifyRedlines };
