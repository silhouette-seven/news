import requests
import json
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from .models import NewsArticle

# A pool of unique, high-quality Unsplash images keyed by category
FALLBACK_IMAGES = {
    "Sports": [
        "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1531415074968-036ba1b575da?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1574629810360-7efbbe195018?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1517649763962-0c623066013b?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?q=80&w=600&auto=format&fit=crop",
    ],
    "Finance": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1560472355-536de3962603?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1554260570-e9689a3418b8?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=600&auto=format&fit=crop",
    ],
    "Technology": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?q=80&w=600&auto=format&fit=crop",
    ],
    "default": [
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1504711434969-e33886168d6c?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1478720568477-152d9b164e26?q=80&w=600&auto=format&fit=crop",
    ],
}

def get_fallback_image(category_name, index):
    """Return a unique fallback image URL based on category and article index."""
    pool = FALLBACK_IMAGES.get(category_name, FALLBACK_IMAGES["default"])
    return pool[index % len(pool)]


def get_weather_data(latitude=11.6643, longitude=78.1460):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&temperature_unit=fahrenheit"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            temp = data['current_weather']['temperature']
            code = data['current_weather']['weathercode']
            if code <= 3:
                desc = "Clear/Partly Cloudy"
            elif code <= 49:
                desc = "Foggy"
            elif code <= 69:
                desc = "Rain"
            elif code <= 79:
                desc = "Snow"
            else:
                desc = "Stormy"
            return int(temp), desc
    except Exception:
        pass
    return None, None


def _annotate_articles(queryset, category_name):
    """Attach a unique fallback_image attribute to each article in a queryset."""
    articles = list(queryset)
    for i, article in enumerate(articles):
        if article.cover_image:
            article.fallback_image = article.cover_image.url
        else:
            article.fallback_image = get_fallback_image(category_name, i)
    return articles


def index_view(request):
    date_str = datetime.now().strftime("%B %d %Y")
    temp_f, weather_desc = get_weather_data()
    location_str = "Salem, TamilNadu"

    # Hero Articles
    hero_qs = NewsArticle.objects.all()[:4]
    hero_list = []
    for i, article in enumerate(hero_qs):
        cat_name = article.category.name if article.category else "default"
        hero_list.append({
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "content": article.content,
            "location": "Global",
            "date": article.published_date.strftime('%B %d, %Y'),
            "image": article.cover_image.url if article.cover_image else get_fallback_image(cat_name, i)
        })

    # Category articles with unique fallback images
    sports_articles = _annotate_articles(
        NewsArticle.objects.filter(category__name__icontains="Sports").order_by('-published_date')[:6],
        "Sports"
    )
    finance_articles = _annotate_articles(
        NewsArticle.objects.filter(category__name__icontains="Finance").order_by('-published_date')[:6],
        "Finance"
    )
    tech_articles = _annotate_articles(
        NewsArticle.objects.filter(category__name__icontains="Tech").order_by('-published_date')[:6],
        "Technology"
    )

    context = {
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': location_str,
        'hero_data': hero_list,
        'hero_articles': hero_qs,
        'sports_articles': sports_articles,
        'finance_articles': finance_articles,
        'tech_articles': tech_articles,
    }
    return render(request, 'index.html', context)


def article_detail_view(request, article_id):
    article = get_object_or_404(NewsArticle, id=article_id)
    cat_name = article.category.name if article.category else "default"
    fallback_image = get_fallback_image(cat_name, article.id)

    # Split content into paragraphs for rich rendering
    paragraphs = [p.strip() for p in article.content.split('\n') if p.strip()]
    if len(paragraphs) <= 1:
        # If content is a single block, split by sentences for readability
        paragraphs = [article.content]

    context = {
        'article': article,
        'fallback_image': fallback_image,
        'paragraphs': paragraphs,
    }
    return render(request, 'article.html', context)
