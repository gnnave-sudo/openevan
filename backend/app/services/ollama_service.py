"""
Layer 1: Intake & Structuring — OllamaService
Extracts structured Fact Packets from raw regulatory text using Ollama LLM.
Falls back to intelligent keyword-based extraction when Ollama is unreachable.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.models import (
    ControlRepresentations,
    FactPacket,
    Obligations,
    RawInput,
)
from app.services.llm_client import get_llm_client

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

# ── Structured extraction keywords ────────────────────────────────────────────

JURISDICTION_PATTERNS = {
    "Singapore": ["singapore", "sg", "mas", "monetary authority"],
    "Hong Kong": ["hong kong", "hk", "hkma", "sfc"],
    "UK": ["uk", "united kingdom", "fca", "prudential regulation"],
    "US": ["us", "united states", "sec", "cftc", "finra"],
    "EU": ["eu", "european union", "esma", "mica"],
    "Australia": ["australia", "asic", "au"],
    "Japan": ["japan", "fsa japan", "jvcea"],
    "UAE": ["uae", "dubai", "var", "dfsa"],
    "Switzerland": ["switzerland", "finma", "ch"],
    "Canada": ["canada", "csa", "osc"],
}

PRODUCT_PATTERNS = {
    "Virtual Asset Exchange": ["exchange", "trading platform", "matching engine"],
    "Custody": ["custody", "custodian", "wallet", "safekeeping"],
    "Lending": ["lending", "borrow", "loan", "credit"],
    "Staking": ["staking", "stake", "yield", "rewards"],
    "DeFi": ["defi", "decentralized finance", "smart contract", "dao"],
    "Payments": ["payment", "remittance", "transfer", "wallet"],
    "NFT": ["nft", "non-fungible", "collectible"],
    "Fund": ["fund", " collective investment", "asset management"],
    "Derivatives": ["derivative", "future", "option", "swap", "cfd"],
}

LICENSING_PATTERNS = {
    "DPT": ["digital payment token", "dpt"],
    "VASP": ["virtual asset service provider", "vasp"],
    "MPI": ["major payment institution", "mpi"],
    "SPI": ["standard payment institution", "spi"],
    "RFMC": ["registered fund management company", "rfmc"],
    "LFMC": ["licensed fund management company", "lfmc"],
    "PTC": ["private trust company", "ptc"],
    "Trust": ["trust company", "trust"],
    "Banking": ["banking", "bank"],
}

REVENUE_PATTERNS = {
    "Transaction Fees": ["transaction fee", "trading fee", "commission"],
    "Subscription": ["subscription", "recurring revenue", "monthly fee"],
    "Spread": ["spread", "markup", "bid-ask"],
    "AUM-based": ["aum", "assets under management", "management fee"],
    "Interest": ["interest", "yield", "lending revenue"],
    "Token": ["token", "coin", "native token"],
}

CUSTODY_PATTERNS = {
    "Third-Party Custody": ["third-party custody", "external custodian"],
    "Self-Custody": ["self custody", "self-custody", "proprietary custody"],
    "Hybrid": ["hybrid custody", "hot cold wallet", "warm wallet"],
    "Non-Custodial": ["non-custodial", "user controlled", "decentralized"],
}

OBLIGATION_KEYWORDS = {
    "licensing_triggers": [
        "licens", "registration", "authorisation", "authorization",
        "permit", "approval", "exemption",
    ],
    "aml_triggers": [
        "aml", "kyc", "cdd", "customer due diligence", "suspicious",
        "transaction monitoring", "travel rule", "fatf", "sanctions",
        "pep", "politically exposed",
    ],
    "reporting_triggers": [
        "reporting", "filing", "submission", "notification",
        "disclos", "transparency", "annual return",
    ],
    "disclosure_requirements": [
        "disclosure", "prospectus", "whitepaper", "terms and conditions",
        "risk warning", "disclaimer", "transparency obligation",
    ],
}

CONTROL_KEYWORDS = {
    "claimed": [
        "existing control", "implemented", "in place", "already",
        "established", "currently deployed",
    ],
    "planned": [
        "planned", "roadmap", "future", "upcoming", "phase 2",
        "next quarter", "implementing",
    ],
    "assumed": [
        "assumed", "subject to", "pending", "upon approval",
        "contingent", "to be confirmed",
    ],
}

CROSS_BORDER_KEYWORDS = [
    "cross-border", "cross border", "multi-jurisdiction", "global",
    "international", "foreign", "overseas", "offshore",
]


class OllamaService:
    """Service for extracting structured fact packets from raw regulatory text.

    Uses LLMClient (multi-provider) as the primary LLM backend, with local
    Ollama as a fallback. Also includes intelligent keyword-based fallback
    extraction when no LLM is available.
    """

    def __init__(self, ollama_url: str = OLLAMA_URL):
        self.ollama_url = ollama_url
        self._llm_client = get_llm_client()

    async def _call_llm_client_json(self, prompt: str, agent_role: str = "normalize_case") -> Optional[Dict[str, Any]]:
        """Delegate to the multi-provider LLMClient for JSON generation."""
        try:
            result = await self._llm_client.generate_json(
                prompt=prompt,
                agent_role=agent_role,
                temperature=0.2,
                max_retries=2,
            )
            if result and not result.get("mock", False):
                return result
            return None
        except Exception as exc:
            logger.debug("LLMClient call failed: %s. Falling back to Ollama.", exc)
            return None

    async def _call_ollama(self, prompt: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "").strip()
        except Exception as exc:
            logger.warning(f"Ollama call failed: {exc}. Using fallback extraction.")
            return None

    def _classify_from_text(
        self, text: str, patterns: Dict[str, List[str]]
    ) -> str:
        text_lower = text.lower()
        best_match = None
        best_score = 0
        for label, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > best_score:
                best_score = score
                best_match = label
        return best_match or "General"

    def _extract_jurisdiction(self, text: str) -> str:
        text_lower = text.lower()
        matches: List[str] = []
        for jurisdiction, keywords in JURISDICTION_PATTERNS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                matches.append(jurisdiction)
        return matches[0] if matches else "Unspecified"

    def _extract_cross_border(self, text: str) -> List[str]:
        text_lower = text.lower()
        elements: List[str] = []
        if any(kw.lower() in text_lower for kw in CROSS_BORDER_KEYWORDS):
            elements.append("Cross-border element identified in description")
        for jurisdiction, keywords in JURISDICTION_PATTERNS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                if jurisdiction not in elements:
                    elements.append(f"Jurisdiction element: {jurisdiction}")
        return elements if elements else ["No explicit cross-border elements"]

    def _extract_obligations(self, text: str) -> Dict[str, List[str]]:
        text_lower = text.lower()
        obligations: Dict[str, List[str]] = {
            "licensing_triggers": [],
            "aml_triggers": [],
            "reporting_triggers": [],
            "disclosure_requirements": [],
        }
        sentences = re.split(r'[.!?\n]+', text)
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            for category, keywords in OBLIGATION_KEYWORDS.items():
                if any(kw.lower() in sentence_lower for kw in keywords):
                    if sentence and sentence not in obligations[category]:
                        obligations[category].append(sentence.strip())
        for category in obligations:
            if not obligations[category]:
                obligations[category] = [
                    f"No explicit {category.replace('_', ' ')} identified"
                ]
        return obligations

    def _extract_controls(self, text: str) -> Dict[str, List[str]]:
        text_lower = text.lower()
        controls: Dict[str, List[str]] = {
            "claimed": [],
            "planned": [],
            "assumed": [],
        }
        sentences = re.split(r'[.!?\n]+', text)
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            for category, keywords in CONTROL_KEYWORDS.items():
                if any(kw.lower() in sentence_lower for kw in keywords):
                    if sentence and sentence not in controls[category]:
                        controls[category].append(sentence.strip())
        for category in controls:
            if not controls[category]:
                controls[category] = [
                    f"No explicit {category} controls identified"
                ]
        return controls

    def _fallback_extraction(self, raw: RawInput) -> FactPacket:
        """Intelligent keyword-based extraction when Ollama is unavailable."""
        logger.info("Running fallback extraction for raw input %s", raw.id)
        content = raw.content
        jurisdiction = self._extract_jurisdiction(content)
        regulator = self._classify_regulator(content, jurisdiction)
        obligations_dict = self._extract_obligations(content)
        controls_dict = self._extract_controls(content)
        return FactPacket(
            raw_input_id=raw.id,
            jurisdiction=jurisdiction,
            regulator=regulator,
            activity_type=self._classify_from_text(content, PRODUCT_PATTERNS),
            product_class=self._classify_from_text(content, PRODUCT_PATTERNS),
            target_user_type=self._classify_user_type(content),
            licensing_category=self._classify_from_text(
                content, LICENSING_PATTERNS
            ),
            revenue_model=self._classify_from_text(content, REVENUE_PATTERNS),
            custody_model=self._classify_from_text(content, CUSTODY_PATTERNS),
            cross_border_elements=self._extract_cross_border(content),
            obligations=Obligations(
                licensing_triggers=obligations_dict["licensing_triggers"][:5],
                aml_triggers=obligations_dict["aml_triggers"][:5],
                reporting_triggers=obligations_dict["reporting_triggers"][:5],
                disclosure_requirements=obligations_dict[
                    "disclosure_requirements"
                ][:5],
            ),
            control_representations=ControlRepresentations(
                claimed=controls_dict["claimed"][:5],
                planned=controls_dict["planned"][:5],
                assumed=controls_dict["assumed"][:5],
            ),
        )

    def _classify_regulator(self, text: str, jurisdiction: str) -> str:
        regulator_map = {
            "Singapore": "MAS",
            "Hong Kong": "HKMA / SFC",
            "UK": "FCA",
            "US": "SEC / CFTC",
            "EU": "ESMA / EBA",
            "Australia": "ASIC",
            "Japan": "JFSA",
            "UAE": "VARA / DFSA",
            "Switzerland": "FINMA",
            "Canada": "CSA",
        }
        return regulator_map.get(jurisdiction, "Unspecified")

    def _classify_user_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["retail", "consumer", "individual"]):
            return "Retail"
        if any(w in text_lower for w in ["accredited", "qualified", "professional", "institutional"]):
            return "Accredited / Professional"
        if any(w in text_lower for w in ["institutional", "corporate", "fund"]):
            return "Institutional"
        return "General Public"

    async def extract_fact_packet(self, raw: RawInput) -> FactPacket:
        """Extract a structured FactPacket from a RawInput using LLMClient, Ollama, or fallback."""
        prompt = self._build_extraction_prompt(raw)

        # Try 1: Multi-provider LLMClient (Gemini, Claude, OpenAI, etc.)
        llm_result = await self._call_llm_client_json(prompt, agent_role="normalize_case")
        if llm_result:
            fact_packet = self._parse_llm_client_response(raw, llm_result)
            if fact_packet:
                logger.info("Fact packet extracted via LLMClient for raw input %s", raw.id)
                return fact_packet

        # Try 2: Local Ollama
        response = await self._call_ollama(prompt)
        if response:
            fact_packet = self._parse_ollama_response(raw, response)
            if fact_packet:
                return fact_packet

        # Try 3: Intelligent keyword-based fallback
        return self._fallback_extraction(raw)

    def _parse_llm_client_response(
        self, raw: RawInput, data: Dict[str, Any]
    ) -> Optional[FactPacket]:
        """Parse a JSON response from LLMClient into a FactPacket."""
        try:
            # Handle both nested and flat structures
            obligations_data = data.get("obligations", {})
            controls_data = data.get("control_representations", {})
            # If obligations is a list, normalize it
            if isinstance(obligations_data, list):
                obligations_data = {
                    "licensing_triggers": [o for o in obligations_data if "licens" in str(o).lower()][:5],
                    "aml_triggers": [o for o in obligations_data if any(k in str(o).lower() for k in ["aml", "kyc", "cdd"])][:5],
                    "reporting_triggers": [o for o in obligations_data if "report" in str(o).lower()][:5],
                    "disclosure_requirements": [o for o in obligations_data if "disclos" in str(o).lower()][:5],
                }
            # Ensure all required keys exist
            for key in ["licensing_triggers", "aml_triggers", "reporting_triggers", "disclosure_requirements"]:
                if key not in obligations_data:
                    obligations_data[key] = [f"No explicit {key.replace('_', ' ')} identified"]
            for key in ["claimed", "planned", "assumed"]:
                if key not in controls_data:
                    controls_data[key] = [f"No explicit {key} controls identified"]
            return FactPacket(
                raw_input_id=raw.id,
                jurisdiction=data.get("jurisdiction", "Unspecified"),
                regulator=data.get("regulator", "Unspecified"),
                activity_type=data.get("activity_type", "General"),
                product_class=data.get("product_class", "General"),
                target_user_type=data.get("target_user_type", "General"),
                licensing_category=data.get("licensing_category", "General"),
                revenue_model=data.get("revenue_model", "Unspecified"),
                custody_model=data.get("custody_model", "Unspecified"),
                cross_border_elements=data.get("cross_border_elements", []),
                obligations=Obligations(
                    licensing_triggers=obligations_data.get("licensing_triggers", [])[:5],
                    aml_triggers=obligations_data.get("aml_triggers", [])[:5],
                    reporting_triggers=obligations_data.get("reporting_triggers", [])[:5],
                    disclosure_requirements=obligations_data.get("disclosure_requirements", [])[:5],
                ),
                control_representations=ControlRepresentations(
                    claimed=controls_data.get("claimed", [])[:5],
                    planned=controls_data.get("planned", [])[:5],
                    assumed=controls_data.get("assumed", [])[:5],
                ),
            )
        except Exception as exc:
            logger.warning("Failed to parse LLMClient response: %s", exc)
            return None

    def _build_extraction_prompt(self, raw: RawInput) -> str:
        return f"""You are a regulatory intelligence extraction system. Extract structured information from the following {raw.input_type}.

CONTENT:
{raw.content}

Extract and return ONLY a JSON object with these exact fields:
{{
  "jurisdiction": "primary jurisdiction (e.g., Singapore, UK, US)",
  "regulator": "primary regulator name",
  "activity_type": "type of activity (e.g., Exchange, Custody, DeFi)",
  "product_class": "product classification",
  "target_user_type": "Retail, Accredited, or Institutional",
  "licensing_category": "DPT, VASP, MPI, Banking, etc.",
  "revenue_model": "Transaction Fees, Subscription, Spread, etc.",
  "custody_model": "Third-Party, Self-Custody, Hybrid, Non-Custodial",
  "cross_border_elements": ["list of cross-border elements"],
  "obligations": {{
    "licensing_triggers": ["list"],
    "aml_triggers": ["list"],
    "reporting_triggers": ["list"],
    "disclosure_requirements": ["list"]
  }},
  "control_representations": {{
    "claimed": ["existing controls"],
    "planned": ["planned controls"],
    "assumed": ["assumed controls"]
  }}
}}

Return ONLY the JSON, no other text."""

    def _parse_ollama_response(
        self, raw: RawInput, response: str
    ) -> Optional[FactPacket]:
        import json as jsonlib
        try:
            text = response.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            data = jsonlib.loads(text)
            obligations_data = data.get("obligations", {})
            controls_data = data.get("control_representations", {})
            return FactPacket(
                raw_input_id=raw.id,
                jurisdiction=data.get("jurisdiction", "Unspecified"),
                regulator=data.get("regulator", "Unspecified"),
                activity_type=data.get("activity_type", "General"),
                product_class=data.get("product_class", "General"),
                target_user_type=data.get("target_user_type", "General"),
                licensing_category=data.get("licensing_category", "General"),
                revenue_model=data.get("revenue_model", "Unspecified"),
                custody_model=data.get("custody_model", "Unspecified"),
                cross_border_elements=data.get(
                    "cross_border_elements", []
                ),
                obligations=Obligations(
                    licensing_triggers=obligations_data.get(
                        "licensing_triggers", []
                    ),
                    aml_triggers=obligations_data.get("aml_triggers", []),
                    reporting_triggers=obligations_data.get(
                        "reporting_triggers", []
                    ),
                    disclosure_requirements=obligations_data.get(
                        "disclosure_requirements", []
                    ),
                ),
                control_representations=ControlRepresentations(
                    claimed=controls_data.get("claimed", []),
                    planned=controls_data.get("planned", []),
                    assumed=controls_data.get("assumed", []),
                ),
            )
        except Exception as exc:
            logger.warning("Failed to parse Ollama response: %s", exc)
            return None
