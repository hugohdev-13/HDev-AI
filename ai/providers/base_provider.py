"""Provider contract and shared article validation."""

from abc import ABC, abstractmethod
from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from core.ai_config import AIConfig


class BaseProvider(ABC):
    """Defines the contract every simulated or real AI provider must meet."""

    def __init__(self, config: type[AIConfig] = AIConfig) -> None:
        self._config = config

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the stable provider identifier."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the configured model identifier."""

    @abstractmethod
    def analyze_article(self, article: Any) -> ArticleAnalysisDTO:
        """Analyze an article and return a normalized DTO."""

    def _validate_article(self, article: Any) -> tuple[str, str]:
        """Validate an article-like object and return safe analysis text."""
        if article is None:
            raise ValueError("An article is required for analysis.")

        title = getattr(article, "title", "")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("The article must have a non-empty title.")

        content = getattr(article, "content", "") or ""
        summary = getattr(article, "summary", "") or ""
        text = content if isinstance(content, str) and content.strip() else summary
        if not isinstance(text, str) or not text.strip():
            raise ValueError("The article must include content or a summary.")

        return title.strip(), text.strip()[: self._config.AI_MAX_ARTICLE_LENGTH]

    def _build_summary(self, text: str) -> str:
        """Build a deterministic mock summary bounded by configured words."""
        words = text.split()[: self._config.AI_SUMMARY_MAX_WORDS]
        return " ".join(words)
