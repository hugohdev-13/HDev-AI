from types import SimpleNamespace
from services.article_category_classifier import ArticleCategoryClassifier
def test_exact_active_category_match():
    category=SimpleNamespace(id=2,name='Python',slug='python',is_active=True)
    assert ArticleCategoryClassifier.classify({'category':' PYTHON '},[category])==2
def test_inactive_or_unknown_category_is_not_assigned():
    category=SimpleNamespace(id=2,name='Python',slug='python',is_active=False)
    assert ArticleCategoryClassifier.classify({'category':'Python'},[category]) is None
