"""Conservative category assignment from existing AI-analysis data."""
from slugify import slugify

class ArticleCategoryClassifier:
    """Assign only an exact active-category match; uncertainty stays uncategorized."""
    MIN_CONFIDENCE = 0.70
    @staticmethod
    def classify(analysis, categories):
        candidate = getattr(analysis, "category", None)
        if isinstance(analysis, dict): candidate = analysis.get("category")
        if not candidate: return None
        confidence = getattr(analysis, "confidence", None) if not isinstance(analysis, dict) else analysis.get("confidence")
        if confidence is not None and float(confidence) < ArticleCategoryClassifier.MIN_CONFIDENCE: return None
        normalized = slugify(str(candidate))
        for category in categories or []:
            if getattr(category, "is_active", False) and normalized in {slugify(category.name), category.slug}:
                return category.id
        return None
