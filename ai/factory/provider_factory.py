"""Factory for provider selection through configuration."""

from ai.providers.azure_provider import AzureProvider
from ai.providers.base_provider import BaseProvider
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAIProvider
from core.ai_config import AIConfig


class ProviderFactory:
    """Creates providers without coupling callers to implementation classes."""

    SUPPORTED_PROVIDERS: dict[str, type[BaseProvider]] = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "azure": AzureProvider,
        "azure_openai": AzureProvider,
        "ollama": OllamaProvider,
    }

    @classmethod
    def create(cls, provider_name: str | None = None) -> BaseProvider:
        """Create the configured provider or raise a clear unsupported error."""
        normalized_name = (provider_name or AIConfig.AI_PROVIDER).strip().lower()
        provider_class = cls.SUPPORTED_PROVIDERS.get(normalized_name)
        if provider_class is None:
            supported_names = ", ".join(sorted(cls.SUPPORTED_PROVIDERS))
            raise ValueError(f"Unsupported AI provider '{normalized_name}'. Supported: {supported_names}.")
        return provider_class()
