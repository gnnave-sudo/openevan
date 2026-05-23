"""
JSON schema validation for model outputs.
"""

import json
import os
from typing import Dict, Any, Tuple, Optional

# jsonschema is optional — validation degrades gracefully if not installed
try:
    from jsonschema import validate, ValidationError
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False
    validate = None
    ValidationError = Exception


logger_import = __import__("logging")
logger = logger_import.getLogger(__name__)

# Cache for loaded schemas
_schema_cache: Dict[str, Dict[str, Any]] = {}


def _load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from file."""
    if schema_name not in _schema_cache:
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..", "schemas",
            f"{schema_name}.schema.json"
        )
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                _schema_cache[schema_name] = json.load(f)
        else:
            _schema_cache[schema_name] = {}
    return _schema_cache[schema_name]


def validate_normalized_case(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate normalized case data against schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not _HAS_JSONSCHEMA:
        return True, None
    try:
        schema = _load_schema("normalized_case")
        if schema:
            validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message} at {list(e.path)}"
    except Exception as e:
        return False, f"Schema load error: {str(e)}"


def validate_scenarios(data: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate scenarios array against schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not _HAS_JSONSCHEMA:
        return True, None
    try:
        schema = _load_schema("scenario")
        if schema:
            validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message} at {list(e.path)}"
    except Exception as e:
        return False, f"Schema load error: {str(e)}"


def validate_agent_output(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate agent output against schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not _HAS_JSONSCHEMA:
        return True, None
    try:
        schema = _load_schema("agent_output")
        if schema:
            validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message} at {list(e.path)}"
    except Exception as e:
        return False, f"Schema load error: {str(e)}"


def validate_adjudication(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate adjudication data against schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not _HAS_JSONSCHEMA:
        return True, None
    try:
        schema = _load_schema("adjudication")
        if schema:
            validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message} at {list(e.path)}"
    except Exception as e:
        return False, f"Schema load error: {str(e)}"


def validate_final_report(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate final report against schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not _HAS_JSONSCHEMA:
        return True, None
    try:
        schema = _load_schema("final_report")
        if schema:
            validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message} at {list(e.path)}"
    except Exception as e:
        return False, f"Schema load error: {str(e)}"


def safe_validate(
    data: Dict[str, Any],
    validator_name: str
) -> Tuple[bool, Optional[str]]:
    """
    Safely validate data with the specified validator.

    Args:
        data: Data to validate
        validator_name: One of: normalized_case, scenarios, agent_output,
                       adjudication, final_report

    Returns:
        Tuple of (is_valid, error_message)
    """
    validators = {
        "normalized_case": validate_normalized_case,
        "scenarios": validate_scenarios,
        "agent_output": validate_agent_output,
        "adjudication": validate_adjudication,
        "final_report": validate_final_report,
    }

    validator = validators.get(validator_name)
    if not validator:
        return False, f"Unknown validator: {validator_name}"

    return validator(data)
