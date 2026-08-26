from unittest.mock import patch

from services.ai_health_service import AIHealthService


class _OpenAIConfig:
    AI_PROVIDER = "openai"
    OPENAI_MODEL = "gpt-4.1-mini"
    AI_AUTO_ANALYZE_ON_CREATE = True


class _GeminiConfig:
    AI_PROVIDER = "gemini"
    GEMINI_MODEL = "mock-gemini"
    AI_AUTO_ANALYZE_ON_CREATE = False


class _DisabledConfig:
    AI_PROVIDER = "disabled"
    AI_AUTO_ANALYZE_ON_CREATE = False


def test_openai_without_key_requires_configuration_and_never_creates_provider():
    with patch("ai.factory.provider_factory.ProviderFactory.create") as create_provider:
        health = AIHealthService(_OpenAIConfig, {}).get_health_status()

    assert health.provider == "OpenAI"
    assert health.model == "gpt-4.1-mini"
    assert health.configured is False
    assert health.status == "configuration_required"
    assert health.message == "El proveedor de IA requiere configuración."
    assert health.editorial_assistant_available is False
    assert health.editorial_review_available is False
    create_provider.assert_not_called()


def test_configured_openai_exposes_no_key_and_is_operational():
    secret = "sk-should-never-be-rendered"
    health = AIHealthService(_OpenAIConfig, {"OPENAI_API_KEY": secret}).get_health_status()

    assert health.status == "operational"
    assert health.configured is True
    assert secret not in health.to_dict().values()


def test_deterministic_provider_is_operational_without_remote_configuration():
    health = AIHealthService(_GeminiConfig, {}).get_health_status()

    assert health.status == "operational"
    assert health.automatic_analysis_enabled is False
    assert health.editorial_assistant_available is True


def test_disabled_provider_is_reported_without_network_activity():
    health = AIHealthService(_DisabledConfig, {}).get_health_status()

    assert health.status == "disabled"
    assert health.message == "La IA está deshabilitada."
    assert health.editorial_review_available is False
