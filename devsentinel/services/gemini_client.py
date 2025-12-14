"""Google Gemini AI client for DevSentinel"""
import logging
from typing import Optional, Dict, Any, Iterable, List

import google.generativeai as genai

from .config import settings

logger = logging.getLogger(__name__)


LEGACY_MODEL_ALIASES = {
    "gemini-pro": "gemini-1.5-pro-latest",
    "gemini-pro-vision": "gemini-1.5-pro-latest",
    "gemini-flash": "gemini-1.5-flash-latest",
    "gemini-1.0-pro": "gemini-1.5-pro-latest",
    "gemini-1.0-pro-vision": "gemini-1.5-pro-latest",
}

FALLBACK_MODELS = [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-pro-vision",
]


class GeminiClient:
    def __init__(self):
        self.model = None
        self._model_name: Optional[str] = None
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured; AI features disabled")
            return

        genai.configure(api_key=settings.GEMINI_API_KEY)
        requested_model = settings.GEMINI_MODEL
        model_candidates: List[str] = list(self._expand_model_candidates(requested_model))

        self.model = self._try_initialize(model_candidates)
        if self.model:
            logger.info("Gemini initialized: %s", self._model_name)
        else:
            logger.error("Gemini init failed; no supported model available")

    @staticmethod
    def _normalize_model_name(model_name: str) -> str:
        alias = LEGACY_MODEL_ALIASES.get(model_name, model_name)
        if alias.startswith("models/"):
            return alias.split("/", 1)[1]
        return alias

    def _expand_model_candidates(self, requested: str) -> Iterable[str]:
        normalized = self._normalize_model_name(requested.strip())
        yield normalized
        prefixed = normalized if normalized.startswith("models/") else f"models/{normalized}"
        if prefixed != normalized:
            yield prefixed
        if normalized != requested:
            # include requested literal in case user already supplied fully qualified name
            yield requested
            if not requested.startswith("models/"):
                yield f"models/{requested}"
        for fallback in FALLBACK_MODELS:
            if fallback not in (normalized, requested):
                yield fallback
                if not fallback.startswith("models/"):
                    yield f"models/{fallback}"

        # Attempt to discover additional models if everything above fails
        try:
            available = genai.list_models()
        except Exception as exc:  # pragma: no cover - network failure
            logger.debug("Gemini list_models failed: %s", exc)
            available = []

        for model in available:
            # Model names from API are in the form models/<name>
            name = getattr(model, "name", "")
            if not name:
                continue
            short_name = name.split("/", 1)[-1]
            methods = getattr(model, "supported_generation_methods", []) or getattr(model, "generation_methods", [])
            if "generateContent" not in methods:
                continue
            if short_name not in (normalized, requested) and short_name not in FALLBACK_MODELS:
                yield short_name

    def _try_initialize(self, candidates: Iterable[str]):
        for candidate in candidates:
            try:
                model = genai.GenerativeModel(candidate)
                self._model_name = candidate
                return model
            except Exception as exc:
                logger.warning("Gemini model '%s' unavailable: %s", candidate, exc)
        return None
    
    def is_available(self) -> bool:
        return self.model is not None
    
    async def _generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': settings.GEMINI_TEMPERATURE,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': max_tokens,
                }
            )
            return response.text if response and response.text else None
        except Exception as e:
            logger.warning("Gemini error using %s: %s", self._model_name or "unknown", e)
            return None
    
    async def generate_incident_analysis(self, title: str, description: str, severity: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        ctx = "\n".join([f"- {k}: {v}" for k, v in (context or {}).items()])
        prompt = f"Analyze incident:\nTitle: {title}\nDescription: {description}\nSeverity: {severity}\n{ctx}\n\nProvide: root cause, impact, priority, affected components."
        return await self._generate(prompt)
    
    async def suggest_resolution_steps(self, title: str, description: str, error_details: Optional[str] = None) -> Optional[str]:
        prompt = f"Suggest resolution:\nTitle: {title}\nDescription: {description}\nError: {error_details or 'N/A'}\n\nProvide: mitigation steps, fix, testing, prevention."
        return await self._generate(prompt, 2048)
    
    async def analyze_code_snippet(self, code: str, language: str = "python", context: Optional[str] = None) -> Optional[str]:
        prompt = f"Analyze {language} code:\n```{language}\n{code}\n```\nContext: {context or 'None'}\n\nIdentify: bugs, security issues, performance problems, best practices, improvements."
        return await self._generate(prompt, 2048)

gemini_client = GeminiClient()
