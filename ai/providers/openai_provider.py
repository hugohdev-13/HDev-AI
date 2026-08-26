"""Remote OpenAI Responses API provider for human-reviewed suggestions."""

import json
import logging
import os
from time import perf_counter
from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.dto.editorial_review import EditorialReviewDTO
from ai.dto.editorial_suggestion import EditorialSuggestionDTO
from ai.prompts.editorial import (
    EDITORIAL_INSTRUCTIONS,
    EDITORIAL_SUGGESTION_SCHEMA,
    build_editorial_input,
)
from ai.prompts.editorial_review import (
    EDITORIAL_REVIEW_INSTRUCTIONS,
    EDITORIAL_REVIEW_SCHEMA,
    build_editorial_review_input,
)
from ai.providers.base_provider import BaseProvider
from core.ai_status import AIProcessingStatus
from core.exceptions import AIProviderNotConfiguredError


logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """Use the official SDK Responses API without mutating editorial models."""

    def __init__(self, client: Any | None = None, config=None) -> None:
        if config is None:
            super().__init__()
        else:
            super().__init__(config=config)
        self._client = client

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._config.OPENAI_MODEL

    def analyze_article(self, article: Any) -> ArticleAnalysisDTO:
        """Map a remote editorial response to the existing analysis contract."""
        suggestion = self._request_editorial_suggestion(article, "analysis")
        return ArticleAnalysisDTO(
            summary=suggestion.suggested_summary,
            suggested_category=suggestion.suggested_category,
            difficulty="",
            technologies=suggestion.technologies,
            keywords=suggestion.keywords,
            sentiment="",
            provider=self.provider_name,
            model_used=self.model_name,
            status=AIProcessingStatus.COMPLETED,
        )

    def generate_editorial_suggestions(
        self,
        article: Any,
    ) -> EditorialSuggestionDTO:
        """Request one strict JSON editorial suggestion from OpenAI."""
        return self._request_editorial_suggestion(article, "editorial_suggestions")

    def review_editorial_quality(self, article: Any) -> EditorialReviewDTO:
        """Request a strict, advisory editorial quality review from OpenAI."""
        payload = self._request_structured_output(
            article=article,
            operation="editorial_review",
            instructions=EDITORIAL_REVIEW_INSTRUCTIONS,
            schema_name="editorial_review",
            schema=EDITORIAL_REVIEW_SCHEMA,
            input_builder=build_editorial_review_input,
        )
        return EditorialReviewDTO.from_dict(
            {
                **payload,
                "status": AIProcessingStatus.COMPLETED,
                "provider": self.provider_name,
                "model": self.model_name,
            }
        )

    def _request_editorial_suggestion(
        self,
        article: Any,
        operation: str,
    ) -> EditorialSuggestionDTO:
        payload = self._request_structured_output(
            article=article,
            operation=operation,
            instructions=EDITORIAL_INSTRUCTIONS,
            schema_name="editorial_suggestion",
            schema=EDITORIAL_SUGGESTION_SCHEMA,
            input_builder=build_editorial_input,
        )
        return EditorialSuggestionDTO.from_dict(
            {
                **payload,
                "status": AIProcessingStatus.COMPLETED,
                "provider": self.provider_name,
                "model": self.model_name,
            }
        )

    def _request_structured_output(
        self,
        *,
        article: Any,
        operation: str,
        instructions: str,
        schema_name: str,
        schema: dict[str, Any],
        input_builder,
    ) -> dict[str, Any]:
        """Execute one bounded Structured Output request shared by editor tools."""
        self._validate_article(article)
        started_at = perf_counter()
        try:
            response = self._get_client().responses.create(
                model=self.model_name,
                instructions=instructions,
                input=input_builder(
                    article,
                    self._config.AI_DEFAULT_LANGUAGE,
                    self._config.AI_MAX_ARTICLE_LENGTH,
                ),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    }
                },
                store=False,
            )
        except Exception as error:
            logger.warning(
                "openai.operation.failed operation=%s model=%s latency_ms=%s "
                "error_type=%s",
                operation,
                self.model_name,
                int((perf_counter() - started_at) * 1000),
                error.__class__.__name__,
            )
            raise
        payload = self._parse_response(response)
        latency_ms = int((perf_counter() - started_at) * 1000)
        usage = getattr(response, "usage", None)
        logger.info(
            "openai.operation.completed operation=%s model=%s latency_ms=%s "
            "input_tokens=%s output_tokens=%s total_tokens=%s",
            operation,
            self.model_name,
            latency_ms,
            getattr(usage, "input_tokens", None),
            getattr(usage, "output_tokens", None),
            getattr(usage, "total_tokens", None),
        )
        return payload

    def _get_client(self):
        if self._client is not None:
            return self._client

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise AIProviderNotConfiguredError(
                "OpenAI provider is not configured."
            )
        try:
            from openai import OpenAI
        except ImportError as error:
            raise AIProviderNotConfiguredError(
                "OpenAI SDK is not installed."
            ) from error

        self._client = OpenAI(
            api_key=api_key,
            timeout=self._config.OPENAI_TIMEOUT_SECONDS,
        )
        return self._client

    @staticmethod
    def _parse_response(response: Any) -> dict[str, Any]:
        response_status = getattr(response, "status", "completed")
        if response_status != "completed":
            raise ValueError("OpenAI response was not completed.")
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise ValueError("OpenAI response did not contain structured output.")
        parsed = json.loads(output_text)
        if not isinstance(parsed, dict):
            raise ValueError("OpenAI structured output must be an object.")
        return parsed
