"""Business rules for category management."""
import re
from slugify import slugify
from models import Category
from repositories.category_repository import CategoryRepository


class CategoryValidationError(ValueError):
    def __init__(self, errors: dict[str, str]): self.errors = errors; super().__init__("Datos de categoría inválidos")


class CategoryDeletionError(ValueError): pass


class CategoryService:
    @staticmethod
    def list_categories(search_term: str, page: int, per_page: int): return CategoryRepository.paginate(search_term, page, per_page)
    @staticmethod
    def get_category(category_id: int): return CategoryRepository.get_by_id(category_id)
    @staticmethod
    def get_active_categories(): return CategoryRepository.list_active()
    @staticmethod
    def _boolean(value) -> bool: return value in (True, "true", "1", "on", 1)
    @staticmethod
    def validate_category_data(data: dict, exclude_id: int | None = None) -> dict:
        result={k:(v.strip() if isinstance(v,str) else v) for k,v in data.items()}; errors={}; name=result.get("name","")
        if not 2<=len(name)<=120: errors["name"]="El nombre debe tener entre 2 y 120 caracteres."
        elif CategoryRepository.name_exists(name,exclude_id): errors["name"]="Ya existe una categoría con ese nombre."
        if len(result.get("description") or "")>500: errors["description"]="La descripción no puede exceder 500 caracteres."
        color=(result.get("color") or "#2563EB").upper()
        if not re.fullmatch(r"#[0-9A-F]{6}",color): errors["color"]="El color debe tener formato #RRGGBB."
        icon=result.get("icon") or "bi-folder"
        if not re.fullmatch(r"bi-[A-Za-z0-9-]{1,97}",icon): errors["icon"]="El icono debe ser un nombre seguro de Bootstrap Icons."
        if errors: raise CategoryValidationError(errors)
        result.update(color=color,icon=icon,is_active=CategoryService._boolean(result.get("is_active")))
        return result
    @staticmethod
    def generate_unique_slug(name: str, exclude_id: int | None = None) -> str:
        base=slugify(name) or "categoria"; slug=base; suffix=2
        while CategoryRepository.slug_exists(slug,exclude_id): slug=f"{base}-{suffix}"; suffix+=1
        return slug
    @staticmethod
    def create_category(data: dict) -> Category:
        data=CategoryService.validate_category_data(data); return CategoryRepository.create(Category(name=data["name"],slug=CategoryService.generate_unique_slug(data["name"]),description=data.get("description") or None,color=data["color"],icon=data["icon"],is_active=data["is_active"]))
    @staticmethod
    def update_category(category_id: int,data: dict) -> Category | None:
        category=CategoryRepository.get_by_id(category_id)
        if category is None:return None
        data=CategoryService.validate_category_data(data,category_id); changed_name=category.name!=data["name"]
        for field in ("name","description","color","icon","is_active"): setattr(category,field,data.get(field) or (False if field=="is_active" else None))
        if changed_name: category.slug=CategoryService.generate_unique_slug(category.name,category_id)
        return CategoryRepository.save(category)
    @staticmethod
    def toggle_category(category_id:int)->Category|None:
        category=CategoryRepository.get_by_id(category_id)
        if category is None:return None
        category.is_active=not category.is_active; return CategoryRepository.save(category)
    @staticmethod
    def delete_category(category_id:int)->bool|None:
        category=CategoryRepository.get_by_id(category_id)
        if category is None:return None
        if CategoryRepository.count_articles(category_id): raise CategoryDeletionError("No se puede eliminar la categoría porque tiene artículos asociados.")
        CategoryRepository.delete(category); return True
