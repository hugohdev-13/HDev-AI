"""Web article routes that delegate optional AI analysis to ArticleService."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from core.ai_status import AIProcessingStatus
from core.audit import log_audit_event
from core.decorators import permission_required
from core.permissions import Permissions
from services.article_service import ArticleService


articles_bp = Blueprint("articles", __name__, url_prefix="/articles")


@articles_bp.get("/")
@login_required
@permission_required(Permissions.ARTICLES_VIEW)
def index():
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    query = ArticleService.search_articles(search)
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    return render_template("articles/index.html", articles=pagination.items, pagination=pagination, search=search)


@articles_bp.get("/new")
@login_required
@permission_required(Permissions.ARTICLES_CREATE)
def new():
    return render_template("articles/form.html")


@articles_bp.post("/")
@login_required
@permission_required(Permissions.ARTICLES_CREATE)
def create():
    result = ArticleService.create_article_with_analysis(_article_form_data())
    log_audit_event("article.created", user_id=current_user.id, article_id=result.article.id)
    if result.ai_analysis.status == AIProcessingStatus.COMPLETED:
        flash("Artículo creado y analizado correctamente.", "success")
    else:
        flash("Artículo creado correctamente.", "success")
        if result.ai_analysis.failed:
            flash("No fue posible completar el análisis de IA.", "warning")
    return redirect(url_for("articles.index"))


@articles_bp.get("/<int:article_id>/edit")
@login_required
@permission_required(Permissions.ARTICLES_EDIT)
def edit(article_id):
    article = ArticleService.get_article(article_id)
    if article is None:
        flash("Artículo no encontrado.", "danger")
        return redirect(url_for("articles.index"))
    return render_template("articles/form.html", article=article)


@articles_bp.post("/<int:article_id>/edit")
@login_required
@permission_required(Permissions.ARTICLES_EDIT)
def update(article_id):
    result = ArticleService.update_article_with_analysis(article_id, _article_form_data())
    if result is None:
        flash("No se encontró el artículo.", "danger")
        return redirect(url_for("articles.index"))

    log_audit_event("article.updated", user_id=current_user.id, article_id=result.article.id)
    if result.ai_analysis.status == AIProcessingStatus.COMPLETED:
        flash("Artículo actualizado y reanalizado correctamente.", "success")
    else:
        flash("Artículo actualizado correctamente.", "success")
        if result.ai_analysis.failed:
            flash("No fue posible actualizar el análisis de IA.", "warning")
    return redirect(url_for("articles.index"))


@articles_bp.post("/<int:article_id>/delete")
@login_required
@permission_required(Permissions.ARTICLES_DELETE)
def delete(article_id):
    deleted = ArticleService.delete_article(article_id)
    if deleted:
        log_audit_event("article.deleted", user_id=current_user.id, article_id=article_id)
        flash("Artículo eliminado correctamente.", "success")
    else:
        flash("No se encontró el artículo.", "danger")
    return redirect(url_for("articles.index"))


def _article_form_data() -> dict[str, str | None]:
    """Build the existing web form payload without exposing request logic to services."""
    return {"title": request.form["title"], "author": request.form.get("author"), "summary": request.form.get("summary"), "content": request.form.get("content"), "status": request.form.get("status", "draft")}
