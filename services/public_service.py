"""Presentation-neutral public landing page data."""
import re

from repositories.public_repository import PublicRepository


class PublicService:
    @staticmethod
    def get_landing_data() -> dict:
        articles = PublicRepository.recent_published()
        return {
            "statistics": PublicRepository.statistics(),
            "recent_articles": articles,
            "tutorials": articles[:3],
            "projects": articles[3:6],
            "categories": PublicService.get_public_categories(),
        }

    @staticmethod
    def get_public_categories(limit: int = 4) -> list[dict]:
        """Return Jinja-safe public category metadata without ORM objects."""
        categories = []
        for category in PublicRepository.public_categories(limit):
            color = category.get("color") or "#2563EB"
            icon = category.get("icon") or "bi-folder"
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                color = "#2563EB"
            if not re.fullmatch(r"bi-[A-Za-z0-9-]{1,97}", icon):
                icon = "bi-folder"
            categories.append(
                {
                    "id": category["id"],
                    "name": category["name"],
                    "slug": category["slug"],
                    "description": category.get("description") or "",
                    "color": color,
                    "icon": icon,
                    "article_count": max(int(category.get("article_count") or 0), 0),
                }
            )
        return categories
