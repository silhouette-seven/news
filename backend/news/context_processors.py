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

# Use a module-level lock or flag to prevent multiple threads from spawning simultaneously
import threading
from django.utils import timezone
from datetime import timedelta
from .models import BreakingNews
from .breaking_news_task import generate_and_store_breaking_news

_is_generating = False
_lock = threading.Lock()

def breaking_news_context(request):
    """
    Context processor to inject the latest Breaking News into all templates.
    If the latest entry is older than 1 hour (or doesn't exist),
    it spawns a background thread to generate a new one.
    """
    global _is_generating

    latest_news = BreakingNews.objects.first()
    now = timezone.now()
    needs_update = False
    
    if latest_news is None:
        needs_update = True
    elif now - latest_news.created_at > timedelta(hours=1):
        needs_update = True

    if needs_update:
        with _lock:
            if not _is_generating:
                _is_generating = True
                
                def run_task():
                    global _is_generating
                    try:
                        generate_and_store_breaking_news()
                    finally:
                        _is_generating = False
                
                thread = threading.Thread(target=run_task)
                thread.daemon = True
                thread.start()

    return {
        'breaking_news': latest_news
    }
