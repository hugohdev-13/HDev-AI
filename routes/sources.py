"""Administrative routes for content sources."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from core.audit import log_audit_event
from core.decorators import permission_required
from core.permissions import Permissions
from services.source_service import SourceDeletionError, SourceService, SourceValidationError

sources_bp = Blueprint("sources", __name__, url_prefix="/sources")

def _data():
    return {key: request.form.get(key) for key in ("name", "website_url", "feed_url", "source_type", "sync_interval_minutes", "is_active")}

@sources_bp.get("/")
@login_required
@permission_required(Permissions.SOURCES_VIEW)
def index():
    search=request.args.get("search", "").strip(); pagination=SourceService.list_sources(search, request.args.get("page", 1, type=int), 10)
    return render_template("sources/index.html", sources=pagination.items, pagination=pagination, search=search, total=pagination.total)

@sources_bp.get("/new")
@login_required
@permission_required(Permissions.SOURCES_CREATE)
def new(): return render_template("sources/form.html", source=None, form_data={}, errors={}, mode="create")

@sources_bp.post("/")
@login_required
@permission_required(Permissions.SOURCES_CREATE)
def create():
    data=_data()
    try: source=SourceService.create_source(data)
    except SourceValidationError as error: return render_template("sources/form.html",source=None,form_data=data,errors=error.errors,mode="create"),400
    log_audit_event("source.created", user_id=current_user.id, source_id=source.id); flash("Fuente creada correctamente.","success")
    return redirect(url_for("sources.index"))

@sources_bp.get("/<int:source_id>/edit")
@login_required
@permission_required(Permissions.SOURCES_EDIT)
def edit(source_id):
    source=SourceService.get_source(source_id)
    if not source: flash("Fuente no encontrada.","danger"); return redirect(url_for("sources.index"))
    return render_template("sources/form.html",source=source,form_data=source,errors={},mode="edit")

@sources_bp.post("/<int:source_id>/edit")
@login_required
@permission_required(Permissions.SOURCES_EDIT)
def update(source_id):
    data=_data()
    try: source=SourceService.update_source(source_id,data)
    except SourceValidationError as error:return render_template("sources/form.html",source={"id":source_id},form_data=data,errors=error.errors,mode="edit"),400
    if not source: flash("Fuente no encontrada.","danger")
    else: log_audit_event("source.updated",user_id=current_user.id,source_id=source.id);flash("Fuente actualizada correctamente.","success")
    return redirect(url_for("sources.index"))

@sources_bp.post("/<int:source_id>/toggle")
@login_required
@permission_required(Permissions.SOURCES_EDIT)
def toggle(source_id):
    source=SourceService.toggle_source(source_id)
    if not source: flash("Fuente no encontrada.","danger")
    else:
        event="source.activated" if source.is_active else "source.deactivated"; log_audit_event(event,user_id=current_user.id,source_id=source.id); flash("Fuente activada correctamente." if source.is_active else "Fuente desactivada correctamente.","success")
    return redirect(url_for("sources.index"))

@sources_bp.post("/<int:source_id>/delete")
@login_required
@permission_required(Permissions.SOURCES_DELETE)
def delete(source_id):
    try: deleted=SourceService.delete_source(source_id)
    except SourceDeletionError as error: flash(str(error),"danger"); return redirect(url_for("sources.index"))
    if deleted: log_audit_event("source.deleted",user_id=current_user.id,source_id=source_id);flash("Fuente eliminada correctamente.","success")
    else: flash("Fuente no encontrada.","danger")
    return redirect(url_for("sources.index"))
