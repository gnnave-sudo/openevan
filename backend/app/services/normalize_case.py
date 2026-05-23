"""
Case normalization service.

Normalizes raw fact patterns into structured case facts for downstream processing.
Uses shared prompt loader and mock factory for consistency.
"""

import json
import logging
from typing import Dict, Any, Tuple, Optional

from app.services.llm_client import get_llm_client
from app.utils.prompt_loader import load_prompt_template
from app.utils.mock_factory import get_mock

logger = logging.getLogger(__name__)


def normalize_case_facts(
    input_facts: Dict[str, Any],
    use_mock: bool = False
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Normalize raw case facts into structured format.

    Args:
        input_facts: Raw fact pattern from user
        use_mock: Whether to return mock data instead of calling LLM

    Returns:
        Tuple of (normalized_case_json, error_message, raw_output)
    """
    if use_mock:
        logger.info("[Normalize] Using mock data")
        return get_mock("normalized_case", **input_facts), None, None

    try:
        prompt_template = load_prompt_template("normalize_case")
        prompt = prompt_template.format(
            activity_name=input_facts.get("activity_name", ""),
            activity_description=input_facts.get("activity_description", ""),
            entities=json.dumps(input_facts.get("entities", [])),
            target_users=json.dumps(input_facts.get("target_users", [])),
            user_flow=input_facts.get("user_flow", ""),
            money_flow=input_facts.get("money_flow", ""),
            custody_flow=input_facts.get("custody_flow", ""),
            marketing_flow=input_facts.get("marketing_flow", ""),
            controls=json.dumps(input_facts.get("controls_in_place", [])),
            assumptions=json.dumps(input_facts.get("assumptions", [])),
        )

        llm = get_llm_client()
        # Note: generate_json is async, but normalize_case_facts is sync.
        # For sync usage, we return the prompt and let async callers handle it.
        # When called from sync code, we use a simplified path.
        try:
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                llm.generate_json(prompt, agent_role="normalize_case")
            )
            if result is None:
                return None, "Failed to normalize case facts", None
            return result, None, None
        except RuntimeError:
            # No event loop running — can't call async from sync context
            logger.info("[Normalize] No event loop — returning mock data")
            return get_mock("normalized_case", **input_facts), None, None

    except FileNotFoundError:
        # Prompt template not found — fall back to mock
        logger.info("[Normalize] Prompt template not found — using mock data")
        return get_mock("normalized_case", **input_facts), None, None
    except Exception as e:
        logger.exception("Case normalization failed")
        return None, f"Case normalization error: {str(e)}", None


async def normalize_case_facts_async(
    input_facts: Dict[str, Any],
    use_mock: bool = False
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Async version of normalize_case_facts.

    Args:
        input_facts: Raw fact pattern from user
        use_mock: Whether to return mock data instead of calling LLM

    Returns:
        Tuple of (normalized_case_json, error_message, raw_output)
    """
    if use_mock:
        logger.info("[Normalize] Using mock data")
        return get_mock("normalized_case", **input_facts), None, None

    try:
        prompt_template = load_prompt_template("normalize_case")
        prompt = prompt_template.format(
            activity_name=input_facts.get("activity_name", ""),
            activity_description=input_facts.get("activity_description", ""),
            entities=json.dumps(input_facts.get("entities", [])),
            target_users=json.dumps(input_facts.get("target_users", [])),
            user_flow=input_facts.get("user_flow", ""),
            money_flow=input_facts.get("money_flow", ""),
            custody_flow=input_facts.get("custody_flow", ""),
            marketing_flow=input_facts.get("marketing_flow", ""),
            controls=json.dumps(input_facts.get("controls_in_place", [])),
            assumptions=json.dumps(input_facts.get("assumptions", [])),
        )

        llm = get_llm_client()
        result = await llm.generate_json(prompt, agent_role="normalize_case")

        if result is None:
            return None, "Failed to normalize case facts", None

        return result, None, None

    except FileNotFoundError:
        # Prompt template not found — fall back to mock
        logger.info("[Normalize] Prompt template not found — using mock data")
        return get_mock("normalized_case", **input_facts), None, None
    except Exception as e:
        logger.exception("Case normalization failed")
        return None, f"Case normalization error: {str(e)}", None
