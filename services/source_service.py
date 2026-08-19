"""Business rules for managing content sources."""

from urllib.parse import urlparse

from slugify import slugify

from models import Source
from repositories.source_repository import SourceRepository


class SourceValidationError(ValueError):
    """Expose field-level validation messages without HTTP coupling."""

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__("Datos de fuente inválidos")


class SourceDeletionError(ValueError):
    """Raised when a source with associated articles is deleted."""


class SourceService:
    """Manage source lifecycle through the repository layer."""

    ALLOWED_SOURCE_TYPES = {"rss", "api", "manual"}

    @staticmethod
    def list_sources(search_term: str, page: int, per_page: int):
        pagination = SourceRepository.paginate(search_term, page, per_page)
        counts = SourceRepository.article_counts([source.id for source in pagination.items])
        for source in pagination.items:
            source.article_count = counts.get(source.id, 0)
        return pagination

    @staticmethod
    def get_source(source_id: int) -> Source | None:
        return SourceRepository.get_by_id(source_id)

    @staticmethod
    def get_active_sources() -> list[Source]:
        return SourceRepository.list_active()

    @staticmethod
    def get_active_rss_sources() -> list[Source]:
        """Return active RSS sources without exposing repository details."""
        return SourceRepository.list_active_rss()

    @staticmethod
    def create_source(data: dict) -> Source:
        data = SourceService.validate_source_data(data)
        source = Source(
            name=data["name"],
            slug=SourceService.generate_unique_slug(data["name"]),
            website_url=data["website_url"] or None,
            feed_url=data["feed_url"] or None,
            source_type=data["source_type"],
            is_active=data["is_active"],
            sync_interval_minutes=data["sync_interval_minutes"],
            last_sync_status="never",
        )
        return SourceRepository.create(source)

    @staticmethod
    def update_source(source_id: int, data: dict) -> Source | None:
        source = SourceRepository.get_by_id(source_id)
        if source is None:
            return None
        data = SourceService.validate_source_data(data, exclude_id=source_id)
        name_changed = source.name != data["name"]
        for field in (
            "name",
            "website_url",
            "feed_url",
            "source_type",
            "is_active",
            "sync_interval_minutes",
        ):
            value = data[field]
            setattr(source, field, value or None if field in {"website_url", "feed_url"} else value)
        if name_changed:
            source.slug = SourceService.generate_unique_slug(source.name, source_id)
        return SourceRepository.save(source)

    @staticmethod
    def toggle_source(source_id: int) -> Source | None:
        source = SourceRepository.get_by_id(source_id)
        if source is None:
            return None
        source.is_active = not source.is_active
        return SourceRepository.save(source)

    @staticmethod
    def delete_source(source_id: int) -> bool | None:
        source = SourceRepository.get_by_id(source_id)
        if source is None:
            return None
        if SourceRepository.count_articles(source_id):
            raise SourceDeletionError(
                "No se puede eliminar la fuente porque tiene artículos asociados."
            )
        SourceRepository.delete(source)
        return True

    @staticmethod
    def generate_unique_slug(name: str, exclude_id: int | None = None) -> str:
        base_slug = slugify(name) or "fuente"
        slug = base_slug
        suffix = 2
        while SourceRepository.slug_exists(slug, exclude_id):
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return slug

    @staticmethod
    def validate_source_data(data: dict, exclude_id: int | None = None) -> dict:
        """Normalize source input and enforce type-dependent invariants."""
        normalized = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }
        errors = {}
        name = normalized.get("name", "")
        website_url = normalized.get("website_url", "") or ""
        feed_url = normalized.get("feed_url", "") or ""
        source_type = (normalized.get("source_type") or "rss").lower()

        if not isinstance(name, str) or not 2 <= len(name) <= 150:
            errors["name"] = "El nombre debe tener entre 2 y 150 caracteres."
        elif SourceRepository.name_exists(name, exclude_id):
            errors["name"] = "Ya existe una fuente con ese nombre."

        SourceService._validate_url(website_url, "website_url", 500, errors)
        SourceService._validate_url(feed_url, "feed_url", 1000, errors)
        if feed_url and SourceRepository.feed_url_exists(feed_url, exclude_id):
            errors["feed_url"] = "Ya existe una fuente con ese feed URL."

        if source_type not in SourceService.ALLOWED_SOURCE_TYPES:
            errors["source_type"] = "El tipo de fuente seleccionado no es válido."
        elif source_type == "rss" and not feed_url:
            errors["feed_url"] = "La URL del feed es obligatoria para una fuente RSS."
        elif source_type == "api" and not website_url and not feed_url:
            errors["source_type"] = "Una fuente API requiere URL del sitio o del feed."

        raw_interval = normalized.get("sync_interval_minutes", 60)
        try:
            sync_interval = 60 if raw_interval in (None, "") else int(raw_interval)
            if not 5 <= sync_interval <= 10080:
                raise ValueError
        except (TypeError, ValueError):
            errors["sync_interval_minutes"] = (
                "El intervalo de sincronización debe estar entre 5 y 10080 minutos."
            )
            sync_interval = 60

        if errors:
            raise SourceValidationError(errors)
        return {
            "name": name,
            "website_url": website_url,
            "feed_url": feed_url,
            "source_type": source_type,
            "is_active": SourceService._normalize_boolean(normalized.get("is_active")),
            "sync_interval_minutes": sync_interval,
        }

    @staticmethod
    def _validate_url(value: str, field: str, maximum_length: int, errors: dict) -> None:
        if not value:
            return
        parsed = urlparse(value)
        if len(value) > maximum_length or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors[field] = "La URL debe ser válida y usar http o https."

    @staticmethod
    def _normalize_boolean(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "on"}
        return value == 1
