"""Article API routes with optional automatic AI analysis metadata."""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from core.audit import log_audit_event
from core.decorators import permission_required
from core.permissions import Permissions
from services.article_service import ArticleMutationResult, ArticleService


api_articles = Blueprint("api_articles", __name__, url_prefix="/api/articles")


@api_articles.get("/")
@login_required
@permission_required(Permissions.ARTICLES_VIEW)
def get_articles():
    articles = ArticleService.get_articles()
    return jsonify([{"id": article.id, "title": article.title, "slug": article.slug, "author": article.author, "status": article.status} for article in articles])


@api_articles.get("/<int:article_id>")
@login_required
@permission_required(Permissions.ARTICLES_VIEW)
def get_article(article_id):
    article = ArticleService.get_article(article_id)
    if article is None:
        return jsonify({"message": "Article not found"}), 404
    return jsonify({"id": article.id, "title": article.title, "slug": article.slug, "summary": article.summary, "content": article.content, "author": article.author, "status": article.status})


@api_articles.post("/")
@login_required
@permission_required(Permissions.ARTICLES_CREATE)
def create_article():
    result = ArticleService.create_article_with_analysis(request.get_json() or {})
    log_audit_event("article.created", user_id=current_user.id, article_id=result.article.id, source="api")
    return jsonify({"message": "Article created", "id": result.article.id, "ai_analysis": _analysis_response(result)}), 201


@api_articles.delete("/<int:article_id>")
@login_required
@permission_required(Permissions.ARTICLES_DELETE)
def delete_article(article_id):
    deleted = ArticleService.delete_article(article_id)
    if deleted is None:
        return jsonify({"message": "Article not found"}), 404
    log_audit_event("article.deleted", user_id=current_user.id, article_id=article_id, source="api")
    return jsonify({"message": "Article deleted"})


def _analysis_response(result: ArticleMutationResult) -> dict[str, bool | str | int | None]:
    """Serialize optional automatic analysis metadata without sensitive details."""
    return result.ai_analysis.to_dict()
