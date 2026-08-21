"""Web article routes that delegate optional AI analysis to ArticleService."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from core.ai_status import AIProcessingStatus
from core.audit import log_audit_event
from core.decorators import permission_required
from core.permissions import Permissions
from services.article_service import ArticleService, ArticleValidationError
from services.article_workflow_service import ArticleWorkflowError, ArticleWorkflowService
from services.category_service import CategoryService


articles_bp = Blueprint("articles", __name__, url_prefix="/articles")


@articles_bp.get("/")
@login_required
@permission_required(Permissions.ARTICLES_VIEW)
def index():
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category", "")
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    filters = ArticleService.normalize_list_filters(search, category_id, status)
    pagination = ArticleService.get_paginated_articles(page=page, **filters)
    return render_template(
        "articles/index.html",
        articles=pagination.items,
        pagination=pagination,
        search=filters["search_term"],
        categories=CategoryService.get_active_categories(),
        selected_category_id=filters["category_id"],
        selected_status=filters["status"],
    )


@articles_bp.get("/new")
@login_required
@permission_required(Permissions.ARTICLES_CREATE)
def new():
    return render_template("articles/form.html", categories=CategoryService.get_active_categories())


@articles_bp.post("/")
@login_required
@permission_required(Permissions.ARTICLES_CREATE)
def create():
    data = _article_form_data()
    try: result = ArticleService.create_article_with_analysis(data)
    except ArticleValidationError as error:
        for message in error.errors.values(): flash(message, "danger")
        return render_template("articles/form.html", article=data, categories=CategoryService.get_active_categories()), 400
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
    if article.status == "published":
        flash(
            "Estás editando un artículo publicado. Los cambios serán visibles en el sitio al guardar.",
            "warning",
        )
    categories = CategoryService.get_active_categories()
    if article.category and not article.category.is_active and article.category not in categories:
        categories.append(article.category)
    return render_template("articles/form.html", article=article, categories=categories)


@articles_bp.get("/<int:article_id>/preview")
@login_required
@permission_required(Permissions.ARTICLES_VIEW)
def preview(article_id):
    """Render a protected, non-mutating public-style editorial preview."""
    article = ArticleService.get_article(article_id)
    if article is None:
        abort(404)
    return render_template(
        "articles/preview.html",
        article=article,
        is_authenticated=current_user.is_authenticated,
    )


@articles_bp.post("/<int:article_id>/edit")
@login_required
@permission_required(Permissions.ARTICLES_EDIT)
def update(article_id):
    data = _article_form_data()
    try: result = ArticleService.update_article_with_analysis(article_id, data)
    except ArticleValidationError as error:
        for message in error.errors.values(): flash(message, "danger")
        data["id"] = article_id
        return render_template("articles/form.html", article=data, categories=CategoryService.get_active_categories()), 400
    if result is None:
        flash("No se encontró el artículo.", "danger")
        return redirect(url_for("articles.index"))

    log_audit_event("article.updated", user_id=current_user.id, article_id=result.article.id)
    if result.workflow_regressed:
        flash("El artículo fue modificado y regresó a revisión.", "warning")
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


@articles_bp.post("/<int:article_id>/status")
@login_required
@permission_required(Permissions.ARTICLES_EDIT)
def transition_status(article_id):
    """Apply a validated editorial transition from the article list."""
    try:
        article = ArticleWorkflowService.transition(
            article_id,
            request.form.get("status"),
            actor=current_user,
        )
    except ArticleWorkflowError as error:
        flash(str(error), "danger")
        return redirect(url_for("articles.index"))
    if article is None:
        flash("No se encontró el artículo.", "danger")
    else:
        log_audit_event(
            "article.status_changed",
            user_id=current_user.id,
            article_id=article.id,
            status=article.status,
        )
        flash("Estado editorial actualizado correctamente.", "success")
    return redirect(url_for("articles.index"))


def _article_form_data() -> dict[str, str | None]:
    """Build the existing web form payload without exposing request logic to services."""
    return {
        "title": request.form.get("title", ""),
        "slug": request.form.get("slug"),
        "author": request.form.get("author"),
        "summary": request.form.get("summary"),
        "content": request.form.get("content"),
        "image_url": request.form.get("image_url"),
        "source_url": request.form.get("source_url"),
        "category_id": request.form.get("category_id"),
    }
