"""
OpenEvan v12 — VOS API Adapter
Bridges the OpenEvan analytical engine with the existing VOS platform on x870.
Translates between v11 REST endpoints and VOS internal formats.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

VOS_BASE = os.environ.get("VOS_API_URL", "http://localhost:8000")
V11_BASE = os.environ.get("V11_API_URL", "http://localhost:8001")


class VOSAdapter:
    """
    Two-way adapter between VOS (port 8000) and OpenEvan v11 (port 8001).
    
    VOS → v11: Convert VOS matter/document events into v11 analytical calls
    v11 → VOS: Push v11 results (stress lab, patterns, credibility) into VOS memory
    """

    def __init__(self, vos_base: str = VOS_BASE, v11_base: str = V11_BASE):
        self.vos = vos_base
        self.v11 = v11_base
        self._client = httpx.AsyncClient(timeout=30)

    async def close(self):
        await self._client.aclose()

    # ── VOS → v11: Forward matter events to analytical engine ───────────────

    async def on_matter_created(self, matter: Dict[str, Any]) -> Dict:
        """When VOS creates a matter, auto-run stress lab assessment."""
        jurisdiction = matter.get("jurisdiction", "Global")
        product = matter.get("product", matter.get("type", "default"))

        # Call v11 stress lab
        resp = await self._client.post(
            f"{self.v11}/api/v1/stresslab/run",
            json={
                "mode": "standard",
                "matter_id": matter.get("id"),
                "context": f"Matter: {matter.get('title', 'Unknown')}",
                "jurisdiction": jurisdiction,
                "product_class": product,
            }
        )
        return resp.json() if resp.status_code == 200 else {"error": f"Stress lab failed: {resp.status_code}"}

    async def on_document_uploaded(self, doc: Dict[str, Any]) -> Dict:
        """When VOS uploads a document, auto-extract fact packet."""
        matter_id = doc.get("matter_id")
        title = doc.get("title", "")

        # Submit to v11 intake
        resp = await self._client.post(
            f"{self.v11}/api/v1/intake/raw-input",
            json={
                "input_type": "internal_memo",
                "source": title,
                "content": f"Document uploaded: {title} (matter: {matter_id})",
            }
        )
        return resp.json() if resp.status_code == 200 else {"error": f"Intake failed: {resp.status_code}"}

    async def on_counsel_memo_received(self, memo: Dict[str, Any]) -> Dict:
        """When counsel memo arrives, run alignment analysis."""
        resp = await self._client.post(
            f"{self.v11}/api/v1/alignment/submit-memo",
            json={
                "counsel_name": memo.get("counsel_name", "Unknown"),
                "memo_content": memo.get("content", ""),
                "matter_id": memo.get("matter_id"),
                "jurisdiction": memo.get("jurisdiction"),
            }
        )
        return resp.json() if resp.status_code == 200 else {"error": f"Alignment failed: {resp.status_code}"}

    # ── v11 → VOS: Push analytical results into VOS ────────────────────────

    async def push_stress_result_to_memory(self, stress_result: Dict[str, Any]) -> Dict:
        """Push stress lab result into VOS memory items."""
        matter_id = stress_result.get("matter_id")
        if not matter_id:
            return {"skipped": "No matter_id"}

        content = json.dumps({
            "type": "stress_lab_result",
            "overall_risk_score": stress_result.get("overall_risk_score"),
            "recommendation": stress_result.get("final_recommendation"),
            "dimensions": stress_result.get("risk_dimensions", []),
            "control_gaps": stress_result.get("key_control_gaps", []),
        }, indent=2)

        resp = await self._client.post(
            f"{self.vos}/api/v1/memory",
            json={
                "memory_class": "risk_signal",
                "title": f"Stress Lab: {stress_result.get('final_recommendation', 'Assessment')}",
                "content": content,
                "importance_score": min(stress_result.get("overall_risk_score", 50) / 100, 1.0),
                "confidence_score": 0.85,
                "source_type": "openevan_v11",
                "source_ref": stress_result.get("id"),
            }
        )
        return {"memory_id": resp.json().get("id") if resp.status_code == 200 else None}

    async def push_pattern_to_memory(self, pattern: Dict[str, Any]) -> Dict:
        """Push extracted pattern into VOS memory as precedent."""
        resp = await self._client.post(
            f"{self.vos}/api/v1/memory",
            json={
                "memory_class": "precedent",
                "title": f"Pattern: {', '.join(pattern.get('risk_drivers', [])[:3])}",
                "content": json.dumps(pattern, indent=2),
                "importance_score": 0.8,
                "confidence_score": 0.75,
                "source_type": "openevan_v11_pattern",
                "source_ref": pattern.get("id"),
            }
        )
        return {"memory_id": resp.json().get("id") if resp.status_code == 200 else None}

    async def create_vos_output(self, analysis: Dict[str, Any], matter_id: str) -> Dict:
        """Create a VOS output from v11 analysis."""
        resp = await self._client.post(
            f"{self.vos}/api/v1/draft/decision-card",
            json={
                "matter_id": matter_id,
                "additional_context": json.dumps(analysis, indent=2),
                "output_type": "decision_card",
            }
        )
        return {"output_id": resp.json().get("output_id") if resp.status_code == 200 else None}

    # ── Bidirectional: Matter enrichment ───────────────────────────────────

    async def enrich_matter(self, matter_id: str) -> Dict[str, Any]:
        """
        Full enrichment pipeline:
        1. Get matter from VOS
        2. Run v11 stress lab
        3. Extract patterns
        4. Push everything back to VOS memory
        """
        # Get matter
        matter_resp = await self._client.get(f"{self.vos}/api/v1/matters/{matter_id}")
        if matter_resp.status_code != 200:
            return {"error": "Matter not found in VOS"}

        matter = matter_resp.json()
        results = {"matter_id": matter_id}

        # Run stress lab
        stress = await self.on_matter_created(matter)
        results["stress_lab"] = stress

        # Extract patterns
        if "id" in stress:
            patterns = await self._client.post(
                f"{self.v11}/api/v1/patterns/extract",
                json={"matter_id": matter_id},
            )
            results["patterns"] = patterns.json() if patterns.status_code == 200 else None

        # Push to VOS memory
        if "id" in stress:
            await self.push_stress_result_to_memory(stress)

        # Create output
        output = await self.create_vos_output(results, matter_id)
        results["output"] = output

        return results

    # ── Health Check ───────────────────────────────────────────────────────

    async def health(self) -> Dict[str, Any]:
        """Check health of both VOS and v11 APIs."""
        vos_health = await self._client.get(f"{self.vos}/health")
        v11_health = await self._client.get(f"{self.v11}/health")

        return {
            "vos": {"status": vos_health.status_code, "healthy": vos_health.status_code == 200},
            "v11": {"status": v11_health.status_code, "healthy": v11_health.status_code == 200},
            "adapter": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }
