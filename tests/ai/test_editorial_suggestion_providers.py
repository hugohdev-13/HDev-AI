"""Ensure current deterministic providers support the editorial contract."""

from types import SimpleNamespace

from ai.factory.provider_factory import ProviderFactory
from core.ai_status import AIProcessingStatus


def test_all_deterministic_providers_generate_editorial_suggestions():
    article = SimpleNamespace(id=1, title="Python con Flask", content="Contenido útil")

    for provider_name in ("gemini", "azure_openai", "ollama"):
        result = ProviderFactory.create(provider_name).generate_editorial_suggestions(
            article
        )

        assert result.status == AIProcessingStatus.COMPLETED
        assert result.suggested_title
        assert result.suggested_content


def test_all_deterministic_providers_generate_editorial_reviews():
    article = SimpleNamespace(id=1, title="Python con Flask", content="Contenido útil")
    for provider_name in ("gemini", "azure_openai", "ollama"):
        result = ProviderFactory.create(provider_name).review_editorial_quality(article)

        assert result.status == AIProcessingStatus.COMPLETED
        assert 0 <= result.overall_score <= 100
