"""
Multi-provider LLM client with model routing and retry handling.
Supports Gemini, Claude (Anthropic), OpenAI, Together, and Moonshot (Kimi).
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class Provider(Enum):
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    TOGETHER = "together"
    MOONSHOT = "moonshot"


@dataclass
class ModelSpec:
    id: str  # LiteLLM format: provider/model-id
    provider: Provider
    is_chat_model: bool = True
    supports_json_mode: bool = False
    supports_tools: bool = False
    context_window: int = 128000
    description: str = ""


# Registry of available models
MODEL_REGISTRY: Dict[str, ModelSpec] = {
    # Gemini
    "gemini-flash": ModelSpec(
        id="gemini/gemini-2.5-flash-preview-05-20",
        provider=Provider.GEMINI,
        supports_json_mode=True,
        context_window=1000000,
        description="Fast, cost-effective for structured outputs"
    ),
    "gemini-pro": ModelSpec(
        id="gemini/gemini-2.5-pro-preview-05-06",
        provider=Provider.GEMINI,
        supports_json_mode=True,
        context_window=1000000,
        description="Complex reasoning and deep analysis"
    ),
    # Claude
    "claude-sonnet": ModelSpec(
        id="anthropic/claude-sonnet-4-20250514",
        provider=Provider.ANTHROPIC,
        supports_tools=True,
        context_window=200000,
        description="Balanced performance and reasoning"
    ),
    "claude-opus": ModelSpec(
        id="anthropic/claude-opus-4-20250514",
        provider=Provider.ANTHROPIC,
        supports_tools=True,
        context_window=200000,
        description="Maximum reasoning depth"
    ),
    # OpenAI
    "gpt-4o": ModelSpec(
        id="openai/gpt-4o",
        provider=Provider.OPENAI,
        supports_json_mode=True,
        supports_tools=True,
        context_window=128000,
        description="General-purpose strong performance"
    ),
    "gpt-4o-mini": ModelSpec(
        id="openai/gpt-4o-mini",
        provider=Provider.OPENAI,
        supports_json_mode=True,
        context_window=128000,
        description="Fast and economical"
    ),
    "o3-mini": ModelSpec(
        id="openai/o3-mini",
        provider=Provider.OPENAI,
        supports_json_mode=True,
        context_window=200000,
        description="Reasoning-optimized"
    ),
    # Together
    "llama-4-scout": ModelSpec(
        id="together/meta-llama/Llama-4-Scout-17B-16E-Instruct",
        provider=Provider.TOGETHER,
        context_window=256000,
        description="Open-source generalist"
    ),
    "llama-4-maverick": ModelSpec(
        id="together/meta-llama/Llama-4-Maverick-17B-128E-Instruct",
        provider=Provider.TOGETHER,
        context_window=256000,
        description="Open-source advanced reasoning"
    ),
    "deepseek-v3": ModelSpec(
        id="together/deepseek-ai/DeepSeek-V3",
        provider=Provider.TOGETHER,
        context_window=64000,
        description="Strong coding and reasoning"
    ),
    "qwen3-235b": ModelSpec(
        id="together/qwen/Qwen3-235B-A22B",
        provider=Provider.TOGETHER,
        context_window=128000,
        description="Multilingual and reasoning"
    ),
    # Moonshot / Kimi
    "kimi-k2": ModelSpec(
        id="moonshot/kimi-k2-0711-preview",
        provider=Provider.MOONSHOT,
        supports_tools=True,
        context_window=256000,
        description="Long-context specialist"
    ),
    "kimi-k2.5": ModelSpec(
        id="moonshot/kimi-k2.5",
        provider=Provider.MOONSHOT,
        supports_tools=True,
        context_window=256000,
        description="Advanced reasoning"
    ),
}


# Default agent-to-model mapping
DEFAULT_AGENT_MODELS = {
    "normalize_case": "gemini-flash",
    "scenario_generator": "gemini-flash",
    "business_advocate": "gemini-flash",
    "compliance_reviewer": "gemini-flash",
    "regulator_proxy": "gemini-pro",
    "neutral_adjudicator": "gemini-pro",
    "final_synthesizer": "gemini-pro",
}


def _load_agent_model_config() -> Dict[str, str]:
    """Load per-agent model overrides from MODEL_CONFIG_JSON env var."""
    config_json = os.getenv("MODEL_CONFIG_JSON", "")
    if not config_json:
        return {}
    try:
        return json.loads(config_json)
    except json.JSONDecodeError:
        return {}


def _get_api_key(provider: Provider) -> Optional[str]:
    """Get API key for a provider from environment."""
    env_vars = {
        Provider.GEMINI: "GEMINI_API_KEY",
        Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
        Provider.OPENAI: "OPENAI_API_KEY",
        Provider.TOGETHER: "TOGETHER_API_KEY",
        Provider.MOONSHOT: "MOONSHOT_API_KEY",
    }
    return os.getenv(env_vars.get(provider, ""))


class StressLabLLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self):
        self.agent_models = {**DEFAULT_AGENT_MODELS, **_load_agent_model_config()}
        self.available_providers: List[str] = []
        self.is_mock = os.getenv("USE_MOCK", "false").lower() == "true"

        for provider in Provider:
            if _get_api_key(provider):
                self.available_providers.append(provider.value)

        # Auto-enable mock mode when no providers are available
        if not self.available_providers and not self.is_mock:
            self.is_mock = True
            import logging
            logging.getLogger(__name__).info(
                "No LLM providers configured — auto-enabling mock mode"
            )

        # LiteLLM proxy URL (optional)
        self.litellm_url = os.getenv("LITELLM_URL", "")

    def get_model_for_agent(self, agent_role: str) -> str:
        """Get the configured model key for an agent role."""
        return self.agent_models.get(agent_role, "gemini-flash")

    def _model_spec(self, model_key: str) -> ModelSpec:
        """Get ModelSpec for a model key."""
        if model_key not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_key}. Available: {list(MODEL_REGISTRY.keys())}")
        return MODEL_REGISTRY[model_key]

    async def generate_json(
        self,
        prompt: str,
        agent_role: str,
        model_key: Optional[str] = None,
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate a JSON response for an agent."""
        if self.is_mock:
            return self._mock_generate_json(prompt, agent_role)

        model_key = model_key or self.get_model_for_agent(agent_role)
        spec = self._model_spec(model_key)

        last_error = None
        for attempt in range(max_retries):
            try:
                return await self._call_provider_json(spec, prompt, temperature)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                continue

        raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")

    async def generate_text(
        self,
        prompt: str,
        agent_role: str,
        model_key: Optional[str] = None,
        temperature: float = 0.3,
        max_retries: int = 3,
    ) -> str:
        """Generate a text response for an agent."""
        if self.is_mock:
            return self._mock_generate_text(prompt, agent_role)

        model_key = model_key or self.get_model_for_agent(agent_role)
        spec = self._model_spec(model_key)

        last_error = None
        for attempt in range(max_retries):
            try:
                return await self._call_provider_text(spec, prompt, temperature)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                continue

        raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")

    async def _call_provider_json(self, spec: ModelSpec, prompt: str, temperature: float) -> Dict[str, Any]:
        """Route JSON generation to the appropriate provider."""
        provider = spec.provider

        if provider == Provider.GEMINI:
            return await self._call_gemini_json(spec, prompt, temperature)
        elif provider == Provider.ANTHROPIC:
            return await self._call_claude_json(spec, prompt, temperature)
        elif provider == Provider.OPENAI:
            return await self._call_openai_json(spec, prompt, temperature)
        elif provider == Provider.TOGETHER:
            return await self._call_together_json(spec, prompt, temperature)
        elif provider == Provider.MOONSHOT:
            return await self._call_moonshot_json(spec, prompt, temperature)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _call_provider_text(self, spec: ModelSpec, prompt: str, temperature: float) -> str:
        """Route text generation to the appropriate provider."""
        provider = spec.provider

        if provider == Provider.GEMINI:
            return await self._call_gemini_text(spec, prompt, temperature)
        elif provider == Provider.ANTHROPIC:
            return await self._call_claude_text(spec, prompt, temperature)
        elif provider == Provider.OPENAI:
            return await self._call_openai_text(spec, prompt, temperature)
        elif provider == Provider.TOGETHER:
            return await self._call_together_text(spec, prompt, temperature)
        elif provider == Provider.MOONSHOT:
            return await self._call_moonshot_text(spec, prompt, temperature)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    # ── Gemini ────────────────────────────────────────────────────────────────

    async def _call_gemini_json(self, spec: ModelSpec, prompt: str, temperature: float) -> Dict[str, Any]:
        import google.generativeai as genai
        api_key = _get_api_key(Provider.GEMINI)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(spec.id.replace("gemini/", ""))
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
        )
        raw = response.text
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)

    async def _call_gemini_text(self, spec: ModelSpec, prompt: str, temperature: float) -> str:
        import google.generativeai as genai
        api_key = _get_api_key(Provider.GEMINI)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(spec.id.replace("gemini/", ""))
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,
            },
        )
        return response.text

    # ── Claude (Anthropic) ────────────────────────────────────────────────────

    async def _call_claude_json(self, spec: ModelSpec, prompt: str, temperature: float) -> Dict[str, Any]:
        import httpx
        api_key = _get_api_key(Provider.ANTHROPIC)
        model_id = spec.id.replace("anthropic/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model_id,
                    "max_tokens": 4096,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["content"][0]["text"]
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)

    async def _call_claude_text(self, spec: ModelSpec, prompt: str, temperature: float) -> str:
        import httpx
        api_key = _get_api_key(Provider.ANTHROPIC)
        model_id = spec.id.replace("anthropic/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model_id,
                    "max_tokens": 4096,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    # ── OpenAI ──────────────────────────────────────────────────────────────

    async def _call_openai_json(self, spec: ModelSpec, prompt: str, temperature: float) -> Dict[str, Any]:
        import httpx
        api_key = _get_api_key(Provider.OPENAI)
        model_id = spec.id.replace("openai/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)

    async def _call_openai_text(self, spec: ModelSpec, prompt: str, temperature: float) -> str:
        import httpx
        api_key = _get_api_key(Provider.OPENAI)
        model_id = spec.id.replace("openai/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ── Together ────────────────────────────────────────────────────────────

    async def _call_together_json(self, spec: ModelSpec, prompt: str, temperature: float) -> Dict[str, Any]:
        import httpx
        api_key = _get_api_key(Provider.TOGETHER)
        model_id = spec.id.replace("together/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)

    async def _call_together_text(self, spec: ModelSpec, prompt: str, temperature: float) -> str:
        import httpx
        api_key = _get_api_key(Provider.TOGETHER)
        model_id = spec.id.replace("together/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ── Moonshot (Kimi) ─────────────────────────────────────────────────────

    async def _call_moonshot_json(self, spec: ModelSpec, prompt: str, temperature: float) -> Dict[str, Any]:
        import httpx
        api_key = _get_api_key(Provider.MOONSHOT)
        model_id = spec.id.replace("moonshot/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)

    async def _call_moonshot_text(self, spec: ModelSpec, prompt: str, temperature: float) -> str:
        import httpx
        api_key = _get_api_key(Provider.MOONSHOT)
        model_id = spec.id.replace("moonshot/", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ── Mock Fallback ───────────────────────────────────────────────────────

    def _mock_generate_json(self, prompt: str, agent_role: str) -> Dict[str, Any]:
        """Return mock JSON for development/testing."""
        return {
            "mock": True,
            "agent_role": agent_role,
            "note": "Running in mock mode — no LLM calls made",
        }

    def _mock_generate_text(self, prompt: str, agent_role: str) -> str:
        return f"[MOCK] Response for {agent_role}. No LLM call was made."


# Singleton
_llm_client: Optional[StressLabLLMClient] = None


def get_llm_client() -> StressLabLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = StressLabLLMClient()
    return _llm_client


def reset_llm_client():
    global _llm_client
    _llm_client = None
