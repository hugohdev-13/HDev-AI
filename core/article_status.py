"""Canonical editorial states and permitted article transitions."""


class ArticleStatus:
    """Avoid scattered editorial status strings across the application."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"

    LABELS = {
        DRAFT: "Borrador",
        REVIEW: "En revisión",
        APPROVED: "Aprobado",
        PUBLISHED: "Publicado",
    }

    TRANSITIONS = {
        DRAFT: {REVIEW},
        REVIEW: {DRAFT, APPROVED},
        APPROVED: {REVIEW, PUBLISHED},
        PUBLISHED: {DRAFT},
    }

    @classmethod
    def is_valid(cls, status: str) -> bool:
        return status in cls.LABELS

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return target in cls.TRANSITIONS.get(current, set())

    @classmethod
    def next_statuses(cls, current: str) -> set[str]:
        return cls.TRANSITIONS.get(current, set())
