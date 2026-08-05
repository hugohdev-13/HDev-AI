"""Presentation-neutral public landing page data."""
from repositories.public_repository import PublicRepository


class PublicService:
    @staticmethod
    def get_landing_data() -> dict:
        articles = PublicRepository.recent_published()
        return {"statistics": PublicRepository.statistics(), "recent_articles": articles, "tutorials": articles[:3], "projects": articles[3:6]}
