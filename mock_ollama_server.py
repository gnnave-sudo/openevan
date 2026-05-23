#!/usr/bin/env python3
"""Mock Ollama server for end-to-end testing of the Evan Legal Quant Stack.
Runs on port 11434 and simulates LLM responses for regulatory extraction tasks."""

import json
import re
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Mock Ollama Server")

class GenerateRequest(BaseModel):
    model: str = "llama3.2"
    prompt: str = ""
    stream: bool = False
    format: str = ""

# ===== Smart extraction responses based on prompt content =====

def extract_from_prompt(prompt: str) -> dict:
    """Parse the prompt to understand what extraction is needed, return structured data."""

    prompt_lower = prompt.lower()
    content = ""
    # Extract the actual document content after instructions
    if "Document:" in prompt:
        content = prompt.split("Document:")[-1].strip()
    elif "Content:" in prompt:
        content = prompt.split("Content:")[-1].strip()
    else:
        content = prompt[-1000:] if len(prompt) > 500 else prompt

    content_lower = content.lower()

    # === JURISDICTION DETECTION ===
    jurisdiction = "Unknown"
    if "singapore" in content_lower or "mas" in content_lower or "psa" in content_lower:
        jurisdiction = "Singapore"
    elif "hong kong" in content_lower or "hk" in content_lower or "sfc" in content_lower:
        jurisdiction = "Hong Kong"
    elif "uk" in content_lower or "fca" in content_lower or "united kingdom" in content_lower:
        jurisdiction = "United Kingdom"
    elif "uae" in content_lower or "dubai" in content_lower or "adgm" in content_lower or "dfsa" in content_lower:
        jurisdiction = "UAE"
    elif "japan" in content_lower or "fsa" in content_lower:
        jurisdiction = "Japan"
    elif "us" in content_lower or "united states" in content_lower or "sec" in content_lower or "fin" in content_lower:
        jurisdiction = "United States"
    elif "australia" in content_lower or "asic" in content_lower:
        jurisdiction = "Australia"

    # === REGULATOR DETECTION ===
    regulator = "Unknown"
    if "mas" in content_lower:
        regulator = "Monetary Authority of Singapore (MAS)"
    elif "sfc" in content_lower:
        regulator = "Securities and Futures Commission (SFC)"
    elif "fca" in content_lower:
        regulator = "Financial Conduct Authority (FCA)"
    elif "dfsa" in content_lower:
        regulator = "Dubai Financial Services Authority (DFSA)"
    elif "adgm" in content_lower:
        regulator = "ADGM Financial Services Regulatory Authority"
    elif "fsa" in content_lower:
        regulator = "Financial Services Agency (JFSA)"
    elif "sec" in content_lower:
        regulator = "Securities and Exchange Commission (SEC)"
    elif "asic" in content_lower:
        regulator = "Australian Securities and Investments Commission (ASIC)"

    # === ACTIVITY TYPE ===
    activity_type = "Digital Asset Service"
    if "yield" in content_lower or "staking" in content_lower:
        activity_type = "Yield/Interest Program"
    elif "custody" in content_lower:
        activity_type = "Custody Service"
    elif "exchange" in content_lower or "trading" in content_lower:
        activity_type = "Exchange/Trading"
    elif "payment" in content_lower or "remittance" in content_lower:
        activity_type = "Payment Service"
    elif "fund" in content_lower:
        activity_type = "Fund Management"

    # === PRODUCT CLASS ===
    product_class = "Digital Payment Token"
    if "yield" in content_lower:
        product_class = "Yield-Bearing Product"
    elif "stablecoin" in content_lower:
        product_class = "Stablecoin"
    elif "nft" in content_lower or "non-fungible" in content_lower:
        product_class = "NFT"
    elif "security token" in content_lower:
        product_class = "Security Token"

    # === TARGET USER ===
    target_user = "Retail"
    if "institutional" in content_lower or "accredited" in content_lower or "qualified" in content_lower:
        target_user = "Accredited/Institutional"
    elif "retail" in content_lower:
        target_user = "Retail"
    elif "professional" in content_lower:
        target_user = "Professional"

    # === LICENSING ===
    licensing = "DPT License"
    if "fund management" in content_lower or "sfa" in content_lower:
        licensing = "DPT License + SFA Fund Management"
    elif "payment" in content_lower:
        licensing = "DPT License + Payment Service"

    # === REVENUE MODEL ===
    revenue_model = "Fee-based"
    if "spread" in content_lower:
        revenue_model = "Yield Spread"
    elif "subscription" in content_lower:
        revenue_model = "Subscription"
    elif "transaction" in content_lower:
        revenue_model = "Transaction Fee"

    # === CUSTODY MODEL ===
    custody_model = "Third-party Custody"
    if "trust" in content_lower:
        custody_model = "Licensed Trust Arrangement"
    elif "self-custody" in content_lower or "proprietary" in content_lower:
        custody_model = "Proprietary/Proprietary Custody"
    elif "multi" in content_lower or "multi-party" in content_lower:
        custody_model = "Multi-party Computation (MPC)"

    # === CROSS-BORDER ===
    cross_border = ["None"]
    if "cross-border" in content_lower or "cross border" in content_lower or "international" in content_lower:
        cross_border = ["Cross-border asset transfers"]
    if "us" in content_lower and jurisdiction != "United States":
        cross_border = [f"Outbound to {cx}" for cx in ["United States"] if jurisdiction != "United States"]

    # === OBLIGATIONS ===
    licensing_triggers = [f"{product_class} service provision"]
    if "yield" in content_lower:
        licensing_triggers.append("Yield/interest generation activity")
    if "custody" in content_lower:
        licensing_triggers.append("Custody of digital tokens")

    aml_triggers = ["Customer onboarding KYC"]
    if "retail" in content_lower:
        aml_triggers.append("Retail customer screening")
    if "high-risk" in content_lower or "high risk" in content_lower:
        aml_triggers.append("High-risk jurisdiction exposure")
    aml_triggers.append("Transaction monitoring")

    reporting_triggers = ["Suspicious transaction reports (STRs)", "Annual compliance reporting"]
    disclosure_requirements = ["Risk disclosure to customers", "Fee structure disclosure"]
    if "retail" in content_lower:
        disclosure_requirements.append("Retail suitability assessment disclosure")

    # === CONTROLS ===
    claimed = ["KYC/AML system operational", "Transaction monitoring active"]
    planned = ["Enhanced due diligence automation"]
    assumed = ["License remains valid", "Regulatory guidance unchanged"]

    return {
        "jurisdiction": jurisdiction,
        "regulator": regulator,
        "activity_type": activity_type,
        "product_class": product_class,
        "target_user_type": target_user,
        "licensing_category": licensing,
        "revenue_model": revenue_model,
        "custody_model": custody_model,
        "cross_border_elements": cross_border,
        "obligations": {
            "licensing_triggers": licensing_triggers,
            "aml_triggers": aml_triggers,
            "reporting_triggers": reporting_triggers,
            "disclosure_requirements": disclosure_requirements
        },
        "control_representations": {
            "claimed": claimed,
            "planned": planned,
            "assumed": assumed
        }
    }


def generate_response(prompt: str) -> str:
    """Generate a structured JSON response based on the prompt content."""
    prompt_lower = prompt.lower()

    # ===== FACT PACKET EXTRACTION =====
    if any(k in prompt_lower for k in ["fact packet", "extract", "structure", "json", "jurisdiction", "regulator"]):
        data = extract_from_prompt(prompt)
        return json.dumps(data, indent=2)

    # ===== COUNSEL MEMO ANALYSIS =====
    if "counsel" in prompt_lower or "legal opinion" in prompt_lower or "memo" in prompt_lower:
        return json.dumps({
            "legal_position": "DPT license sufficient for yield program",
            "risk_assessment": "Low risk",
            "key_assumptions": ["No SFA fund management trigger", "MAS guidance unchanged"],
            "recommended_controls": ["Standard disclosures", "Retail risk warnings"],
            "confidence_level": "High"
        }, indent=2)

    # ===== SCENARIO SIMULATION =====
    if "scenario" in prompt_lower or "simulate" in prompt_lower or "agent" in prompt_lower:
        return json.dumps({
            "business_advocate": "The proposed activity falls within existing DPT licensing scope. No additional licensing required. Revenue model is standard and custody arrangement is compliant.",
            "compliance_reviewer": "While the activity appears within scope, there are regulatory nuances around the yield mechanism that warrant deeper review. Recommend enhanced monitoring.",
            "regulator_proxy": "MAS has signaled increased scrutiny on yield-bearing products. The SFA fund management licensing trigger must be formally assessed before proceeding.",
            "neutral_adjudicator": "The business case is sound but regulatory ambiguity around yield programs requires formal clarification. HOLD pending MAS guidance.",
            "risk_assessment": "Medium-High",
            "recommendation": "HOLD"
        }, indent=2)

    # ===== DEFAULT =====
    return json.dumps({
        "analysis": "Regulatory document analyzed",
        "key_points": ["Licensing requirements identified", "Control gaps noted", "Recommendation pending"],
        "recommendation": "Review required"
    }, indent=2)


@app.get("/api/tags")
async def list_models():
    """Return available models."""
    return {
        "models": [
            {
                "name": "llama3.2",
                "model": "llama3.2",
                "modified_at": "2026-05-18T00:00:00Z",
                "size": 2019483520,
                "digest": "mock-digest",
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "3.2B",
                    "quantization_level": "Q4_K_M"
                }
            }
        ]
    }


@app.post("/api/generate")
async def generate(req: Request):
    """Generate a response for the given prompt."""
    body = await req.json()
    prompt = body.get("prompt", "")
    stream = body.get("stream", False)

    response_text = generate_response(prompt)

    if stream:
        async def stream_response():
            # Stream response in chunks
            chunks = [response_text[i:i+20] for i in range(0, len(response_text), 20)]
            for chunk in chunks:
                yield json.dumps({"response": chunk, "done": False}) + "\n"
            yield json.dumps({"response": "", "done": True, "total_duration": 1500000000, "load_duration": 500000000, "prompt_eval_duration": 300000000, "eval_duration": 700000000}) + "\n"

        return StreamingResponse(stream_response(), media_type="application/x-ndjson")
    else:
        return JSONResponse({
            "model": body.get("model", "llama3.2"),
            "created_at": "2026-05-18T12:00:00Z",
            "response": response_text,
            "done": True,
            "done_reason": "stop",
            "total_duration": 1500000000,
            "load_duration": 500000000,
            "prompt_eval_duration": 300000000,
            "eval_count": 150,
            "eval_duration": 700000000
        })


@app.get("/api/version")
async def version():
    return {"version": "0.6.5"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=11434, log_level="info")
