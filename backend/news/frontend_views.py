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
    "Politics": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1555848962-6e79363ec58f?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1575320181282-9afab399332c?q=80&w=600&auto=format&fit=crop",
    ],
    "Entertainment": [
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1478720568477-152d9b164e26?q=80&w=600&auto=format&fit=crop",
    ],
    "Science & Health": [
        "https://images.unsplash.com/photo-1532094349884-543bc11b234d?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1576086213369-97a306d36557?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1507413245164-6160d8298b31?q=80&w=600&auto=format&fit=crop",
    ],
    "Environment": [
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1466611653911-95081537e5b7?q=80&w=600&auto=format&fit=crop",
    ],
    "Israel-Iran War": [
        "https://images.unsplash.com/photo-1580752300992-559f8e79ce98?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1547036967-23d11aacaee0?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1573455494060-c5595004fb6c?q=80&w=600&auto=format&fit=crop",
    ],
    "Local News": [
        "https://images.unsplash.com/photo-1477587458883-47145ed94245?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?q=80&w=600&auto=format&fit=crop",
    ],
    "Opinion": [
        "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1504711434969-e33886168d6c?q=80&w=600&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=600&auto=format&fit=crop",
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

    # Helper to build section data
    def _get_section(category_filter, fallback_key, limit=6):
        return _annotate_articles(
            NewsArticle.objects.filter(category__name__icontains=category_filter).order_by('-published_date')[:limit],
            fallback_key
        )

    # Build all sections — each is a dict with title, articles, and layout class
    sections = [
        {"title": "Trending: Israel-Iran War", "articles": _get_section("Israel-Iran", "Israel-Iran War"), "layout": "grid-feature-heavy", "accent": "#c0392b"},
        {"title": "Sports", "articles": _get_section("Sports", "Sports"), "layout": "grid-guardian", "accent": "#8B4513"},
        {"title": "Finance", "articles": _get_section("Finance", "Finance"), "layout": "grid-three-col", "accent": "#2c3e50"},
        {"title": "Technology", "articles": _get_section("Tech", "Technology"), "layout": "grid-guardian", "accent": "#1a5276"},
        {"title": "Politics", "articles": _get_section("Politics", "Politics"), "layout": "grid-feature-heavy", "accent": "#6c3483"},
        {"title": "Entertainment", "articles": _get_section("Entertainment", "Entertainment"), "layout": "grid-masonry", "accent": "#d35400"},
        {"title": "Science & Health", "articles": _get_section("Science", "Science & Health"), "layout": "grid-three-col", "accent": "#1abc9c"},
        {"title": "Environment", "articles": _get_section("Environment", "Environment"), "layout": "grid-masonry", "accent": "#27ae60"},
        {"title": "Local News", "articles": _get_section("Local", "Local News"), "layout": "grid-list-view", "accent": "#7f8c8d"},
        {"title": "Opinion & Editorial", "articles": _get_section("Opinion", "Opinion"), "layout": "grid-list-view", "accent": "#34495e"},
    ]

    # Filter out sections with no articles
    sections = [s for s in sections if s['articles']]

    context = {
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': location_str,
        'hero_data': hero_list,
        'hero_articles': hero_qs,
        'sections': sections,
    }
    return render(request, 'index.html', context)


def article_detail_view(request, article_id):
    article = get_object_or_404(NewsArticle, id=article_id)
    cat_name = article.category.name if article.category else "default"
    fallback_image = get_fallback_image(cat_name, article.id)

    # Record implicit READ interaction for authenticated users
    if request.user.is_authenticated:
        from users.models import UserInteraction, UserTagScore
        # Only record one READ per user/article pair per session (avoid spamming)
        if not UserInteraction.objects.filter(
            user=request.user, article=article, interaction_type='READ'
        ).exists():
            UserInteraction.objects.create(
                user=request.user, article=article, interaction_type='READ'
            )
        # Always bump tag scores (handles re-reads with lighter weight)
        UserTagScore.bump_for_article(request.user, article, 'READ')

    # Split content into paragraphs for rich rendering
    paragraphs = [p.strip() for p in article.content.split('\n') if p.strip()]
    if len(paragraphs) <= 1:
        # If content is a single block, split by sentences for readability
        paragraphs = [article.content]

    # Weather/date for base template
    from datetime import datetime
    date_str = datetime.now().strftime("%B %d %Y")
    temp_f, weather_desc = get_weather_data()

    context = {
        'article': article,
        'fallback_image': fallback_image,
        'paragraphs': paragraphs,
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': "Salem, TamilNadu",
    }
    return render(request, 'article.html', context)

