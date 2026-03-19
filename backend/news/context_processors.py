from news.models import Category
from django.utils.text import slugify


def nav_sections_processor(request):
    """Inject nav_sections into every template for the shared section nav bar."""
    categories = Category.objects.all().order_by('name')
    nav_sections = [
        {"title": cat.name, "slug": slugify(cat.name), "accent": "#ffffff"}
        for cat in categories
    ]
    return {'nav_sections': nav_sections}
