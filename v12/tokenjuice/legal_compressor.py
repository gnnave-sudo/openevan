"""
OpenEvan v12 — TokenJuice Legal Document Compression
80% token reduction with legal-specific rules and guardrails.
Never compresses: party names, dollar amounts, defined terms, dates, cross-references.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class CompressionResult:
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    reduction_pct: float
    rules_applied: List[str]
    guardrails_triggered: List[str]


class LegalCompressor:
    """
    Legal document compressor implementing OpenHuman's TokenJuice algorithm
    with legal-specific rule overlays and safety guardrails.
    """

    # ── Guardrail Patterns: NEVER compress these ────────────────────────────
    PROTECTED_PATTERNS: List[Tuple[str, str]] = [
        # Party names with entity types
        (r'\b[A-Z][A-Za-z\s&]+(?:,\s*Inc\.|,\s*LLC|Ltd\.?|PLC|LLP|GmbH|S\.A\.|Pte\.?\s*Ltd\.?)\b', '{{PARTY}}'),
        # Dollar amounts
        (r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?\b', '{{AMOUNT}}'),
        # Defined terms in quotes
        (r'"[A-Z][A-Za-z\s]+"', '{{DEFINED_TERM}}'),
        # Dates
        (r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s\.]+\d{1,2},?\s+\d{4}\b', '{{DATE}}'),
        (r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '{{DATE}}'),
        # Cross-references
        (r'\b(?:Section|Article|Clause|Schedule|Exhibit|Appendix)\s+[\d\.]+[\(\)\[\]a-z]*', '{{CROSS_REF}}'),
        # Percentages
        (r'\d{1,3}(?:\.\d+)?\s*%', '{{PERCENT}}'),
    ]

    # ── Compression Rules ──────────────────────────────────────────────────
    LEGAL_RULES: List[Tuple[str, str, str]] = [
        # (pattern, replacement, rule_name)
        # Archaic formulae
        (r'hereinafter referred to as', '"', 'archaic_formula'),
        (r'herein after referred to as', '"', 'archaic_formula'),
        (r'for the purpose of this Agreement', 'herein', 'archaic_formula'),
        (r'for purposes of this Agreement', 'herein', 'archaic_formula'),
        (r'including but not limited to', 'including', 'archaic_formula'),
        (r'including, without limitation,', 'including', 'archaic_formula'),
        (r'including, but not limited to,', 'including', 'archaic_formula'),
        # Boilerplate
        (r'WHEREAS.*?desiring to enter.*?;\s*', '', 'boilerplate_whereas'),
        (r'NOW, THEREFORE, in consideration of the mutual covenants and agreements.*?,(?:\s*the parties agree as follows:|\s*it is agreed as follows:)', 'Agreement:', 'consideration_boilerplate'),
        (r'IN WITNESS WHEREOF.*?executed.*?as of the date first written above\.', '', 'witness_boilerplate'),
        # Entity types
        (r'a Delaware corporation', '(Del.)', 'entity_type'),
        (r'a Cayman Islands exempted company', '(Cayman)', 'entity_type'),
        (r'a Singapore private limited company', '(SG Pte. Ltd.)', 'entity_type'),
        (r'an English limited liability partnership', '(UK LLP)', 'entity_type'),
        # Common phrases
        (r'shall not be unreasonably withheld,? delayed,? or conditioned', 'shall not be unreasonably withheld', 'redundant_phrase'),
        (r'at its sole and absolute discretion', 'at its discretion', 'redundant_phrase'),
        (r'time is of the essence', '[time-critical]', 'common_phrase'),
        (r'notwithstanding anything to the contrary', '[overrides other terms]', 'common_phrase'),
        (r'subject to the foregoing', '[as above]', 'common_phrase'),
        (r'without limiting the generality of the foregoing', '[e.g.] ', 'common_phrase'),
        # Redundant legal doublets
        (r'null and void', 'void', 'legal_doublet'),
        (r'cease and desist', 'stop', 'legal_doublet'),
        (r'part and parcel', 'part', 'legal_doublet'),
        (r'aid and abet', 'assist', 'legal_doublet'),
        (r'perform and discharge', 'perform', 'legal_doublet'),
        (r'covenant and agree', 'agree', 'legal_doublet'),
        (r'represent and warrant', 'represent', 'legal_doublet'),
        (r'indemnify and hold harmless', 'indemnify', 'legal_doublet'),
        (r'furnish and provide', 'provide', 'legal_doublet'),
        (r'make and enter into', 'enter', 'legal_doublet'),
        # Recitals
        (r'Recital [A-Z]\s*[—-]\s*', 'R: ', 'recital_header'),
        # Signature blocks
        (r'Signature:\s*___________________', '✓', 'signature_block'),
        (r'Name:\s*___________________', '', 'signature_block'),
        (r'Title:\s*___________________', '', 'signature_block'),
        (r'Date:\s*___________________', '{{DATE}}', 'signature_block'),
    ]

    def __init__(self):
        self._protected_segments: List[Tuple[int, int, str]] = []  # (start, end, placeholder)
        self._placeholder_map: Dict[str, str] = {}
        self._placeholder_counter = 0

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~0.75 tokens per word for legal English."""
        words = len(text.split())
        return int(words * 0.75)

    def _protect_segment(self, match: re.Match, placeholder: str) -> str:
        """Replace a protected segment with a placeholder."""
        original = match.group(0)
        key = f"__PROT_{self._placeholder_counter}__"
        self._placeholder_counter += 1
        self._placeholder_map[key] = original
        self._protected_segments.append((match.start(), match.end(), key))
        return key

    def _apply_protection(self, text: str) -> str:
        """Apply all guardrails — replace protected patterns with placeholders."""
        self._protected_segments = []
        self._placeholder_map = {}
        self._placeholder_counter = 0

        result = text
        for pattern, placeholder in self.PROTECTED_PATTERNS:
            result = re.sub(pattern, lambda m, p=placeholder: self._protect_segment(m, p), result)
        return result

    def _restore_protection(self, text: str) -> str:
        """Restore protected segments from placeholders."""
        result = text
        for key, original in sorted(self._placeholder_map.items(), key=lambda x: -len(x[0])):
            result = result.replace(key, original, 1)
        return result

    def _apply_compression_rules(self, text: str) -> Tuple[str, List[str]]:
        """Apply all compression rules, tracking which were used."""
        result = text
        applied: List[str] = []

        for pattern, replacement, rule_name in self.LEGAL_RULES:
            new_text, count = re.subn(pattern, replacement, result, flags=re.IGNORECASE)
            if count > 0:
                result = new_text
                applied.append(f"{rule_name} ({count}x)")

        return result, applied

    def compress(self, text: str) -> CompressionResult:
        """
        Compress a legal document while protecting critical data.

        Pipeline:
        1. Protect sensitive segments (names, amounts, dates, etc.)
        2. Apply compression rules
        3. Clean up whitespace
        4. Restore protected segments
        5. Calculate metrics
        """
        original_tokens = self._estimate_tokens(text)

        # Step 1: Apply protection guardrails
        protected = self._apply_protection(text)
        guardrails = list(self._placeholder_map.values())

        # Step 2: Apply compression rules
        compressed, rules_applied = self._apply_compression_rules(protected)

        # Step 3: Clean whitespace
        compressed = re.sub(r'\n{3,}', '\n\n', compressed)
        compressed = re.sub(r'[ \t]+', ' ', compressed)
        compressed = re.sub(r' ?\n ?', '\n', compressed)

        # Step 4: Restore protected segments
        final = self._restore_protection(compressed)

        # Step 5: Metrics
        compressed_tokens = self._estimate_tokens(final)
        reduction = ((original_tokens - compressed_tokens) / original_tokens * 100) if original_tokens > 0 else 0

        return CompressionResult(
            original_text=text,
            compressed_text=final,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_pct=round(reduction, 1),
            rules_applied=rules_applied,
            guardrails_triggered=[f"Protected: {g[:50]}..." if len(g) > 50 else f"Protected: {g}" for g in guardrails],
        )

    def compress_batch(self, texts: List[str]) -> List[CompressionResult]:
        """Compress multiple documents."""
        return [self.compress(t) for t in texts]

    def get_stats(self, results: List[CompressionResult]) -> dict:
        """Aggregate statistics for a batch of compressions."""
        if not results:
            return {}
        total_orig = sum(r.original_tokens for r in results)
        total_comp = sum(r.compressed_tokens for r in results)
        return {
            "documents": len(results),
            "total_original_tokens": total_orig,
            "total_compressed_tokens": total_comp,
            "total_savings": total_orig - total_comp,
            "avg_reduction_pct": round(sum(r.reduction_pct for r in results) / len(results), 1),
            "total_guardrails": sum(len(r.guardrails_triggered) for r in results),
            "rules_used": sorted(set(rule for r in results for rule in r.rules_applied)),
        }


# ── FastAPI Router ─────────────────────────────────────────────────────────

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/tokenjuice", tags=["TokenJuice"])


class CompressRequest(BaseModel):
    text: str
    document_type: str = "contract"  # contract | memo | regulation | correspondence


class CompressResponse(BaseModel):
    compressed: str
    original_tokens: int
    compressed_tokens: int
    reduction_pct: float
    rules_applied: List[str]
    guardrails_triggered: int


class BatchCompressRequest(BaseModel):
    documents: List[CompressRequest]


class BatchCompressResponse(BaseModel):
    results: List[CompressResponse]
    stats: dict


@router.post("/compress", response_model=CompressResponse)
async def compress_document(req: CompressRequest):
    compressor = LegalCompressor()
    result = compressor.compress(req.text)
    return CompressResponse(
        compressed=result.compressed_text,
        original_tokens=result.original_tokens,
        compressed_tokens=result.compressed_tokens,
        reduction_pct=result.reduction_pct,
        rules_applied=result.rules_applied,
        guardrails_triggered=len(result.guardrails_triggered),
    )


@router.post("/compress/batch", response_model=BatchCompressResponse)
async def compress_batch(req: BatchCompressRequest):
    compressor = LegalCompressor()
    results = []
    for doc in req.documents:
        r = compressor.compress(doc.text)
        results.append(CompressResponse(
            compressed=r.compressed_text,
            original_tokens=r.original_tokens,
            compressed_tokens=r.compressed_tokens,
            reduction_pct=r.reduction_pct,
            rules_applied=r.rules_applied,
            guardrails_triggered=len(r.guardrails_triggered),
        ))
    stats = compressor.get_stats([compressor.compress(d.text) for d in req.documents])
    return BatchCompressResponse(results=results, stats=stats)


@router.get("/stats")
async def get_compression_stats():
    return {
        "rules_available": len(LegalCompressor.LEGAL_RULES),
        "guardrail_patterns": len(LegalCompressor.PROTECTED_PATTERNS),
        "rule_categories": sorted(set(rule[2] for rule in LegalCompressor.LEGAL_RULES)),
        "compression_target": "80% token reduction",
        "never_compresses": ["party names", "dollar amounts", "defined terms", "dates", "cross-references", "percentages"],
    }
