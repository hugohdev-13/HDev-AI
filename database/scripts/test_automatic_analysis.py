"""Create one article through the production service and log AI analysis output."""

import logging

from app import app
from services.article_service import ArticleService


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Execute the automatic analysis pipeline inside the Flask app context."""
    payload = {
        "title": "Prueba automática de análisis IA",
        "summary": "Contenido de prueba para validar la creación del análisis.",
        "content": (
            "Este artículo se crea mediante ArticleService y debe generar "
            "exactamente un registro de análisis asociado."
        ),
        "status": "draft",
    }

    with app.app_context():
        result = ArticleService.create_article_with_analysis(payload)

    logger.info(
        "Manual automatic analysis result article_id=%s triggered=%s "
        "analysis_id=%s status=%s failed=%s",
        result.article.id,
        result.ai_analysis.triggered,
        result.ai_analysis.analysis_id,
        result.ai_analysis.status,
        result.ai_analysis.failed,
    )


if __name__ == "__main__":
    main()
