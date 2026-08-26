"""Provider contract and shared article validation."""

from abc import ABC, abstractmethod
from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.dto.editorial_review import EditorialReviewDTO
from ai.dto.editorial_suggestion import EditorialSuggestionDTO
from core.ai_config import AIConfig
from core.ai_status import AIProcessingStatus


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

    def generate_editorial_suggestions(
        self,
        article: Any,
    ) -> EditorialSuggestionDTO:
        """Build deterministic suggestions shared by all current mock providers."""
        title, text = self._validate_article(article)
        analysis = self.analyze_article(article)
        return EditorialSuggestionDTO(
            suggested_title=f"{title}: guía práctica",
            suggested_summary=self._build_summary(text),
            suggested_content=(
                f"{text}\n\n"
                "Añade contexto, ejemplos verificables y una conclusión para el lector."
            ),
            suggested_category=analysis.suggested_category,
            keywords=analysis.keywords,
            technologies=analysis.technologies,
            notes="Sugerencia generada para revisión humana; no se ha guardado ningún cambio.",
            status=AIProcessingStatus.COMPLETED,
            provider=self.provider_name,
            model=self.model_name,
        )

    def review_editorial_quality(self, article: Any) -> EditorialReviewDTO:
        """Build a predictable advisory review for deterministic providers."""
        title, text = self._validate_article(article)
        summary = str(getattr(article, "summary", "") or "").strip()
        summary_score = 80 if summary else 35
        issues = [] if summary else ["El resumen está ausente o requiere más contexto."]
        recommendations = (
            []
            if summary
            else ["Añade un resumen que explique el contexto y el valor para el lector."]
        )
        return EditorialReviewDTO(
            overall_score=78 if summary else 65,
            clarity_score=78,
            structure_score=76,
            summary_quality_score=summary_score,
            title_content_alignment_score=80 if title and text else 0,
            readability_score=77,
            factual_risk_level="medium",
            publication_readiness="ready" if summary else "needs_review",
            strengths=["El contenido proporciona una base clara para revisión editorial."],
            issues=issues,
            recommendations=recommendations,
            missing_information=["Verifica las afirmaciones factuales antes de publicar."],
            status=AIProcessingStatus.COMPLETED,
            provider=self.provider_name,
            model=self.model_name,
        )
