// OpenEvan v12 — Neo4j Legal Knowledge Graph Schema
// Party-Contract-Clause-Risk entity relationships
// Run this in Neo4j Browser or via cypher-shell

// ── Constraints & Indexes ─────────────────────────────────────────────────

CREATE CONSTRAINT party_name IF NOT EXISTS
  FOR (p:Party) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT contract_id IF NOT EXISTS
  FOR (c:Contract) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT clause_id IF NOT EXISTS
  FOR (cl:Clause) REQUIRE cl.id IS UNIQUE;

CREATE CONSTRAINT risk_id IF NOT EXISTS
  FOR (r:Risk) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT obligation_id IF NOT EXISTS
  FOR (o:Obligation) REQUIRE o.id IS UNIQUE;

CREATE INDEX contract_status_idx IF NOT EXISTS
  FOR (c:Contract) ON (c.status);

CREATE INDEX clause_type_idx IF NOT EXISTS
  FOR (cl:Clause) ON (cl.type);

CREATE INDEX risk_severity_idx IF NOT EXISTS
  FOR (r:Risk) ON (r.severity);

CREATE INDEX party_role_idx IF NOT EXISTS
  FOR (p:Party) ON (p.role);

// ── Sample Data: Employment Agreement ─────────────────────────────────────

// Create parties
CREATE (employer:Party {
  name: 'Acme Technologies, Inc.',
  role: 'employer',
  type: 'corporation',
  jurisdiction: 'Delaware',
  incorporation_date: date('2015-03-12')
})

CREATE (executive:Party {
  name: 'Jane Smith',
  role: 'employee',
  type: 'individual',
  jurisdiction: 'Singapore',
  nationality: 'US'
})

CREATE (advisor:Party {
  name: 'Wong & Partners LLC',
  role: 'legal_counsel',
  type: 'law_firm',
  jurisdiction: 'Singapore',
  sra_number: 'SRA-2023-8842'
})

// Create contract
CREATE (contract:Contract {
  id: 'emp-2026-001',
  title: 'Employment Agreement',
  type: 'employment',
  status: 'active',
  governing_law: 'Singapore',
  jurisdiction: 'Singapore',
  executed_date: date('2026-01-15'),
  effective_date: date('2026-02-01'),
  expiration_date: date('2028-01-31'),
  currency: 'SGD',
  total_value: 480000,
  csl_source: 'csl://contracts/emp-2026-001.json',
  created_at: datetime(),
  updated_at: datetime()
})

// Create clauses
CREATE (termClause:Clause {
  id: 'emp-001-cl-01',
  type: 'term',
  title: 'Term of Employment',
  section_number: '1',
  text: 'The Company shall employ the Executive for a fixed term of twenty-four (24) months...',
  risk_level: 'low',
  negotiable: false,
  created_at: datetime()
})

CREATE (compClause:Clause {
  id: 'emp-001-cl-02',
  type: 'compensation',
  title: 'Compensation',
  section_number: '2',
  text: 'The Executive shall receive an annual base salary of SGD 240,000...',
  risk_level: 'low',
  negotiable: true,
  created_at: datetime()
})

CREATE (confClause:Clause {
  id: 'emp-001-cl-03',
  type: 'confidentiality',
  title: 'Confidentiality',
  section_number: '5',
  text: 'The Executive agrees to maintain the confidentiality of all proprietary information...',
  risk_level: 'medium',
  negotiable: false,
  created_at: datetime()
})

CREATE (restrictClause:Clause {
  id: 'emp-001-cl-04',
  type: 'non_compete',
  title: 'Non-Competition',
  section_number: '7',
  text: 'The Executive shall not, for a period of twelve (12) months following termination...',
  risk_level: 'high',
  negotiable: true,
  created_at: datetime()
})

CREATE (ipClause:Clause {
  id: 'emp-001-cl-05',
  type: 'intellectual_property',
  title: 'Intellectual Property',
  section_number: '8',
  text: 'All work product created during employment shall be the sole property of the Company...',
  risk_level: 'medium',
  negotiable: true,
  created_at: datetime()
})

CREATE (termClause2:Clause {
  id: 'emp-001-cl-06',
  type: 'termination',
  title: 'Termination',
  section_number: '9',
  text: 'Either party may terminate this Agreement with ninety (90) days written notice...',
  risk_level: 'high',
  negotiable: true,
  created_at: datetime()
})

// Create risks
CREATE (risk1:Risk {
  id: 'emp-001-risk-01',
  severity: 'P1',
  category: 'regulatory',
  description: 'Non-compete clause may be unenforceable under Singapore Employment Act amendments (2025)',
  probability: 0.75,
  financial_impact: 50000,
  regulatory_body: 'MOM Singapore',
  created_at: datetime()
})

CREATE (risk2:Risk {
  id: 'emp-001-risk-02',
  severity: 'P2',
  category: 'operational',
  description: '90-day termination notice period creates resource planning uncertainty',
  probability: 0.60,
  financial_impact: 20000,
  created_at: datetime()
})

CREATE (risk3:Risk {
  id: 'emp-001-risk-03',
  severity: 'P1',
  category: 'legal',
  description: 'IP assignment clause does not exclude pre-existing work — may conflict with open source contributions',
  probability: 0.80,
  financial_impact: 100000,
  created_at: datetime()
})

// Create obligations
CREATE (obl1:Obligation {
  id: 'emp-001-obl-01',
  type: 'regulatory',
  description: 'Comply with Singapore Employment Act and CPF contribution requirements',
  deadline: date('2026-02-01'),
  status: 'pending',
  assignee: 'employer',
  created_at: datetime()
})

CREATE (obl2:Obligation {
  id: 'emp-001-obl-02',
  type: 'contractual',
  description: 'Procure directors and officers (D&O) liability insurance',
  deadline: date('2026-02-15'),
  status: 'pending',
  assignee: 'employer',
  created_at: datetime()
})

// ── Relationships ─────────────────────────────────────────────────────────

CREATE (employer)-[:PARTY_TO { role: 'employer', signed_date: date('2026-01-15') }]->(contract)
CREATE (executive)-[:PARTY_TO { role: 'employee', signed_date: date('2026-01-15') }]->(contract)
CREATE (advisor)-[:ADVISES { scope: 'employment_law', engagement_date: date('2025-12-01') }]->(contract)

CREATE (contract)-[:CONTAINS { order: 1 }]->(termClause)
CREATE (contract)-[:CONTAINS { order: 2 }]->(compClause)
CREATE (contract)-[:CONTAINS { order: 5 }]->(confClause)
CREATE (contract)-[:CONTAINS { order: 7 }]->(restrictClause)
CREATE (contract)-[:CONTAINS { order: 8 }]->(ipClause)
CREATE (contract)-[:CONTAINS { order: 9 }]->(termClause2)

CREATE (restrictClause)-[:HAS_RISK]->(risk1)
CREATE (termClause2)-[:HAS_RISK]->(risk2)
CREATE (ipClause)-[:HAS_RISK]->(risk3)

CREATE (contract)-[:HAS_OBLIGATION { priority: 'high' }]->(obl1)
CREATE (contract)-[:HAS_OBLIGATION { priority: 'medium' }]->(obl2)

CREATE (advisor)-[:REPRESENTS]->(employer)
CREATE (risk1)-[:MITIGATED_BY { strategy: 'jurisdiction_review' }]->(advisor)

// ── Essential Queries ─────────────────────────────────────────────────────

// Q1: Find all contracts for a party
// MATCH (p:Party {name: 'Acme Technologies, Inc.'})-[:PARTY_TO]->(c:Contract)
// RETURN c.title, c.type, c.status, c.effective_date

// Q2: Find all P1 risks across active contracts
// MATCH (c:Contract {status: 'active'})-[:CONTAINS]->(cl:Clause)-[:HAS_RISK]->(r:Risk {severity: 'P1'})
// RETURN c.title, cl.type, r.description, r.probability, r.financial_impact

// Q3: Find related parties through shared contracts
// MATCH (p1:Party)-[:PARTY_TO]->(c:Contract)<-[:PARTY_TO]-(p2:Party)
// WHERE p1 <> p2
// RETURN p1.name, p2.name, count(c) as shared_contracts

// Q4: Get full contract graph
// MATCH (c:Contract {id: 'emp-2026-001'})-[:CONTAINS]->(cl:Clause)
// OPTIONAL MATCH (cl)-[:HAS_RISK]->(r:Risk)
// OPTIONAL MATCH (c)-[:HAS_OBLIGATION]->(o:Obligation)
// RETURN c, collect(DISTINCT cl) as clauses, collect(DISTINCT r) as risks, collect(DISTINCT o) as obligations

// Q5: Risk heatmap by contract
// MATCH (c:Contract)-[:CONTAINS]->(cl:Clause)-[:HAS_RISK]->(r:Risk)
// RETURN c.title, count(r) as risk_count,
//        sum(CASE r.severity WHEN 'P1' THEN 4 WHEN 'P2' THEN 2 ELSE 1 END) as weighted_score
// ORDER BY weighted_score DESC

// Q6: Obligations approaching deadline
// MATCH (c:Contract)-[:HAS_OBLIGATION]->(o:Obligation)
// WHERE o.status = 'pending' AND o.deadline < date() + duration('P30D')
// RETURN c.title, o.description, o.deadline, o.assignee
// ORDER BY o.deadline

// Q7: Counsel workload
// MATCH (counsel:Party {role: 'legal_counsel'})-[:ADVISES]->(c:Contract)
// RETURN counsel.name, count(c) as active_contracts, collect(c.title) as contracts
// ORDER BY active_contracts DESC

// Q8: Cross-contract risk patterns
// MATCH (cl:Clause {type: 'non_compete'})-[:HAS_RISK]->(r:Risk)
// RETURN cl.type, count(r) as occurrences, collect(DISTINCT r.category) as categories

// Q9: Contract party network (for visualization)
// MATCH (p1:Party)-[:PARTY_TO]->(c:Contract)<-[:PARTY_TO]-(p2:Party)
// WHERE p1 <> p2
// RETURN p1.name as source, p2.name as target, c.title as contract, c.type as type

// Q10: Compliance posture score
// MATCH (c:Contract {status: 'active'})
// OPTIONAL MATCH (c)-[:HAS_OBLIGATION]->(o:Obligation {status: 'completed'})
// OPTIONAL MATCH (c)-[:CONTAINS]->(cl:Clause)-[:HAS_RISK]->(r:Risk)
// RETURN
//   count(DISTINCT c) as total_contracts,
//   count(DISTINCT o) as completed_obligations,
//   count(DISTINCT r) as open_risks,
//   avg(CASE WHEN r IS NULL THEN 100 ELSE 100 - (r.probability * 25) END) as avg_posture_score
