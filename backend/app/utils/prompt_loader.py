"""
Shared prompt template loader with LRU caching and hot-reload support.

Replaces duplicated load_prompt_template() patterns across service files.
"""

import os
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Base path for prompt templates
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


@lru_cache(maxsize=32)
def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the prompts directory with LRU caching.

    Args:
        template_name: Name of the template file (e.g., "business_advocate")

    Returns:
        Template text string

    Raises:
        FileNotFoundError: If template file does not exist
    """
    template_path = os.path.join(PROMPTS_DIR, f"{template_name}.txt")
    with open(template_path, "r", encoding="utf-8") as f:
        text = f.read()
    logger.debug("Loaded prompt template: %s (%d chars)", template_name, len(text))
    return text


def clear_prompt_cache() -> None:
    """Clear the prompt template cache. Call after prompt files are updated."""
    load_prompt_template.cache_clear()
    logger.info("Prompt template cache cleared")


def list_available_templates() -> list:
    """List all available prompt template names."""
    templates = []
    if os.path.isdir(PROMPTS_DIR):
        for fname in os.listdir(PROMPTS_DIR):
            if fname.endswith(".txt"):
                templates.append(fname[:-4])
    return sorted(templates)


def get_prompt_info(template_name: str) -> dict:
    """Get metadata about a prompt template."""
    template_path = os.path.join(PROMPTS_DIR, f"{template_name}.txt")
    if not os.path.exists(template_path):
        return {"exists": False, "name": template_name}
    stat = os.stat(template_path)
    return {
        "exists": True,
        "name": template_name,
        "path": template_path,
        "size_bytes": stat.st_size,
        "modified_at": stat.st_mtime,
    }
