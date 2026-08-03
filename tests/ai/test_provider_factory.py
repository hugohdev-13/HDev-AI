"""Unit tests for provider selection."""

import unittest

from ai.factory.provider_factory import ProviderFactory
from ai.providers.azure_provider import AzureProvider
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAIProvider


class ProviderFactoryTestCase(unittest.TestCase):
    """Verifies supported provider mappings."""

    def test_create_returns_expected_provider(self) -> None:
        self.assertIsInstance(ProviderFactory.create("openai"), OpenAIProvider)
        self.assertIsInstance(ProviderFactory.create("gemini"), GeminiProvider)
        self.assertIsInstance(ProviderFactory.create("azure_openai"), AzureProvider)
        self.assertIsInstance(ProviderFactory.create("ollama"), OllamaProvider)

    def test_create_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError):
            ProviderFactory.create("unknown")
