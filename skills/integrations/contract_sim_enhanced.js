/**
 * contract_sim v11-enhanced
 * Runs contract clause simulation through the CSL Stress Lab before returning results.
 * Integrates with OpenEvan v11 analytical engine.
 * 
 * Usage: node contract_sim_enhanced.js --contract <file> --jurisdiction <jurisdiction>
 */

const fs = require('fs');
const path = require('path');

// Import v11 client (adjust path as needed)
let v11;
try {
  v11 = require('./v11_client');
} catch {
  // Fallback: use inline fetch if v11_client not available
  const V11_BASE = process.env.V11_API_URL || 'http://localhost:8001';
  v11 = {
    stresslab: {
      simulate: async (body) => {
        const res = await fetch(`${V11_BASE}/api/v1/stresslab/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        return res.json();
      },
    },
    patterns: {
      extract: async (body) => {
        const res = await fetch(`${V11_BASE}/api/v1/patterns/extract`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        return res.json();
      },
    },
  };
}

async function analyzeContract(contractPath, jurisdiction = 'Global', productClass = 'default') {
  console.error(`[contract_sim] Reading ${contractPath}...`);
  const content = fs.readFileSync(contractPath, 'utf-8');
  
  // Step 1: Quick clause extraction (existing logic)
  const clauses = extractClauses(content);
  console.error(`[contract_sim] Found ${clauses.length} material clauses`);
  
  // Step 2: Run CSL stress lab on the contract
  console.error('[contract_sim] Running CSL stress simulation...');
  const stressResult = await v11.stresslab.simulate({
    mode: 'standard',
    context: `Contract review: ${path.basename(contractPath)} — ${clauses.slice(0, 3).map(c => c.type).join(', ')}`,
    product_class: productClass,
    jurisdiction: jurisdiction,
  });
  
  // Step 3: Extract patterns from stress result
  console.error('[contract_sim] Extracting compliance patterns...');
  const patternResult = await v11.patterns.extract({
    stress_result_id: stressResult.id,
  });
  
  // Step 4: Build enhanced output
  const output = {
    contract: path.basename(contractPath),
    jurisdiction,
    clauses: clauses.length,
    clause_details: clauses,
    risk_assessment: {
      overall_risk_score: stressResult.overall_risk_score,
      recommendation: stressResult.final_recommendation,
      dimensions: stressResult.risk_dimensions,
    },
    agent_positions: stressResult.scenarios?.[0]?.agent_positions || [],
    control_gaps: stressResult.key_control_gaps || [],
    obligations: patternResult.recurring_obligations || [],
    risk_drivers: patternResult.risk_drivers || [],
    generated_at: new Date().toISOString(),
  };
  
  return output;
}

function extractClauses(text) {
  // Simple clause extraction — in production this uses NLP
  const clauseTypes = [
    { type: 'indemnification', pattern: /indemnif|hold harmless/gi },
    { type: 'termination', pattern: /terminat|break.*clause/gi },
    { type: 'limitation_of_liability', pattern: /limit.*liability|liability.*cap/gi },
    { type: 'governing_law', pattern: /govern.*law|jurisdiction/gi },
    { type: 'force_majeure', pattern: /force majeure|act of god/gi },
    { type: 'confidentiality', pattern: /confidential|non-disclosure|nda/gi },
    { type: 'data_protection', pattern: /data protection|gdpr|pdpa/gi },
    { type: 'aml_compliance', pattern: /aml|anti.money|kyc/gi },
    { type: 'regulatory_compliance', pattern: /regulatory|compliance.*oblig/gi },
    { type: 'intellectual_property', pattern: /intellectual property|ip.*rights/gi },
  ];
  
  const found = [];
  for (const { type, pattern } of clauseTypes) {
    const matches = text.match(pattern);
    if (matches) {
      const contextIdx = text.search(pattern);
      const context = text.slice(Math.max(0, contextIdx - 60), contextIdx + 120);
      found.push({
        type,
        occurrences: matches.length,
        risk_level: _assessClauseRisk(type, context),
        context: context.replace(/\s+/g, ' ').trim(),
      });
    }
  }
  return found;
}

function _assessClauseRisk(type, context) {
  const riskMap = {
    indemnification: 'high',
    limitation_of_liability: 'high',
    data_protection: 'critical',
    aml_compliance: 'critical',
    regulatory_compliance: 'critical',
    termination: 'medium',
    confidentiality: 'medium',
    intellectual_property: 'medium',
    force_majeure: 'low',
    governing_law: 'low',
  };
  
  // Check for red flags
  const redFlags = /unlimited|sole.*discretion|waive.*right|no.*liability|absolutely/gi;
  const baseRisk = riskMap[type] || 'medium';
  if (redFlags.test(context)) {
    const escalation = { low: 'medium', medium: 'high', high: 'critical' };
    return escalation[baseRisk] || 'critical';
  }
  return baseRisk;
}

// CLI entry point
async function main() {
  const args = process.argv.slice(2);
  const contractIdx = args.indexOf('--contract');
  const jurisIdx = args.indexOf('--jurisdiction');
  const productIdx = args.indexOf('--product');
  
  if (contractIdx === -1 || !args[contractIdx + 1]) {
    console.error('Usage: node contract_sim_enhanced.js --contract <file> [--jurisdiction <j>] [--product <p>]');
    process.exit(1);
  }
  
  const contractPath = args[contractIdx + 1];
  const jurisdiction = jurisIdx !== -1 ? args[jurisIdx + 1] : 'Global';
  const productClass = productIdx !== -1 ? args[productIdx + 1] : 'default';
  
  try {
    const result = await analyzeContract(contractPath, jurisdiction, productClass);
    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.error(`[contract_sim] ERROR: ${err.message}`);
    // Fallback: return basic analysis without v11
    const content = fs.readFileSync(contractPath, 'utf-8');
    const clauses = extractClauses(content);
    console.log(JSON.stringify({
      contract: path.basename(contractPath),
      jurisdiction,
      clauses: clauses.length,
      clause_details: clauses,
      risk_assessment: { overall_risk_score: 0, recommendation: 'UNKNOWN', dimensions: [], note: 'v11 API unavailable' },
      fallback: true,
    }, null, 2));
  }
}

if (require.main === module) {
  main();
}

module.exports = { analyzeContract, extractClauses };
