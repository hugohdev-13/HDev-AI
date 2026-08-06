"""Administrative category routes delegating all rules to CategoryService."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from core.audit import log_audit_event
from core.decorators import permission_required
from core.permissions import Permissions
from services.category_service import CategoryDeletionError, CategoryService, CategoryValidationError

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

def _data(): return {"name":request.form.get("name",""),"description":request.form.get("description",""),"color":request.form.get("color","#2563EB"),"icon":request.form.get("icon","bi-folder"),"is_active":request.form.get("is_active")}
@categories_bp.get("/")
@login_required
@permission_required(Permissions.CATEGORIES_VIEW)
def index():
    search=request.args.get("search","").strip(); pagination=CategoryService.list_categories(search,request.args.get("page",1,type=int),10)
    return render_template("categories/index.html",categories=pagination.items,pagination=pagination,search=search,total=pagination.total)
@categories_bp.get("/new")
@login_required
@permission_required(Permissions.CATEGORIES_CREATE)
def new(): return render_template("categories/form.html",category=None,form_data={},errors={},mode="create")
@categories_bp.post("/")
@login_required
@permission_required(Permissions.CATEGORIES_CREATE)
def create():
    data=_data()
    try: category=CategoryService.create_category(data)
    except CategoryValidationError as error:return render_template("categories/form.html",category=None,form_data=data,errors=error.errors,mode="create"),400
    log_audit_event("category.created",user_id=current_user.id,category_id=category.id);flash("Categoría creada correctamente.","success");return redirect(url_for("categories.index"))
@categories_bp.get("/<int:category_id>/edit")
@login_required
@permission_required(Permissions.CATEGORIES_EDIT)
def edit(category_id):
    category=CategoryService.get_category(category_id)
    if not category: flash("Categoría no encontrada.","danger");return redirect(url_for("categories.index"))
    return render_template("categories/form.html",category=category,form_data=category,errors={},mode="edit")
@categories_bp.post("/<int:category_id>/edit")
@login_required
@permission_required(Permissions.CATEGORIES_EDIT)
def update(category_id):
    data=_data()
    try: category=CategoryService.update_category(category_id,data)
    except CategoryValidationError as error:return render_template("categories/form.html",category={"id":category_id},form_data=data,errors=error.errors,mode="edit"),400
    if not category:flash("Categoría no encontrada.","danger")
    else:log_audit_event("category.updated",user_id=current_user.id,category_id=category.id);flash("Categoría actualizada correctamente.","success")
    return redirect(url_for("categories.index"))
@categories_bp.post("/<int:category_id>/toggle")
@login_required
@permission_required(Permissions.CATEGORIES_EDIT)
def toggle(category_id):
    category=CategoryService.toggle_category(category_id)
    if not category:flash("Categoría no encontrada.","danger")
    else:
        event="category.activated" if category.is_active else "category.deactivated";log_audit_event(event,user_id=current_user.id,category_id=category.id);flash("Categoría activada correctamente." if category.is_active else "Categoría desactivada correctamente.","success")
    return redirect(url_for("categories.index"))
@categories_bp.post("/<int:category_id>/delete")
@login_required
@permission_required(Permissions.CATEGORIES_DELETE)
def delete(category_id):
    try: result=CategoryService.delete_category(category_id)
    except CategoryDeletionError as error:flash(str(error),"danger");return redirect(url_for("categories.index"))
    if result:log_audit_event("category.deleted",user_id=current_user.id,category_id=category_id);flash("Categoría eliminada correctamente.","success")
    else:flash("Categoría no encontrada.","danger")
    return redirect(url_for("categories.index"))
