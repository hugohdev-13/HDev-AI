"""Configuration-only AI health assessment with no provider invocation."""

import os
from collections.abc import Mapping

from ai.dto.ai_health_status import AIHealthStatus
from core.ai_config import AIConfig


class AIHealthService:
    """Derive a safe provider state without network calls or token consumption."""

    _MODELS = {
        "openai": "OPENAI_MODEL",
        "gemini": "GEMINI_MODEL",
        "azure": "AZURE_OPENAI_MODEL",
        "azure_openai": "AZURE_OPENAI_MODEL",
        "ollama": "OLLAMA_MODEL",
    }

    def __init__(
        self,
        config: type[AIConfig] = AIConfig,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._config = config
        self._environment = environment if environment is not None else os.environ

    def get_health_status(self) -> AIHealthStatus:
        """Return configuration health; never instantiate or call a provider."""
        provider = str(getattr(self._config, "AI_PROVIDER", "") or "").strip().lower()
        automatic_analysis_enabled = bool(
            getattr(self._config, "AI_AUTO_ANALYZE_ON_CREATE", False)
        )
        if provider in {"", "disabled", "none"}:
            return self._status(
                provider="Deshabilitado",
                model="",
                configured=False,
                status="disabled",
                message="La IA está deshabilitada.",
                automatic_analysis_enabled=automatic_analysis_enabled,
            )

        model_attribute = self._MODELS.get(provider)
        model = str(getattr(self._config, model_attribute, "") or "") if model_attribute else ""
        provider_label = {
            "openai": "OpenAI",
            "azure": "Azure OpenAI",
            "azure_openai": "Azure OpenAI",
        }.get(provider, provider.title())
        if provider == "openai" and not str(self._environment.get("OPENAI_API_KEY", "")).strip():
            return self._status(
                provider=provider_label,
                model=model,
                configured=False,
                status="configuration_required",
                message="El proveedor de IA requiere configuración.",
                automatic_analysis_enabled=automatic_analysis_enabled,
            )
        if model_attribute is None:
            return self._status(
                provider=provider_label,
                model="",
                configured=False,
                status="configuration_required",
                message="El proveedor de IA requiere configuración.",
                automatic_analysis_enabled=automatic_analysis_enabled,
            )
        return self._status(
            provider=provider_label,
            model=model,
            configured=True,
            status="operational",
            message="El proveedor de IA está disponible.",
            automatic_analysis_enabled=automatic_analysis_enabled,
        )

    @staticmethod
    def _status(
        *,
        provider: str,
        model: str,
        configured: bool,
        status: str,
        message: str,
        automatic_analysis_enabled: bool,
    ) -> AIHealthStatus:
        return AIHealthStatus(
            provider=provider,
            model=model,
            configured=configured,
            status=status,
            message=message,
            automatic_analysis_enabled=automatic_analysis_enabled,
            editorial_assistant_available=configured,
            editorial_review_available=configured,
        )
