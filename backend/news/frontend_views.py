import requests
import json
import re
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import NewsArticle


from django.utils.text import slugify
from news.models import Category

from .utils import get_wikimedia_image

def get_fallback_image(category_name, index):
    """Return a globally relevant image URL based on category and article index via WikiMedia."""
    return get_wikimedia_image(category_name, index)


def get_user_location(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    if ip == '127.0.0.1' or ip == 'localhost':
        # Default for local testing
        return "Salem", "Tamil Nadu", 11.6643, 78.1460

    try:
        url = f"http://ip-api.com/json/{ip}"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data['status'] == 'success':
                return data['city'], data['regionName'], data['lat'], data['lon']
    except Exception:
        pass
        
    return "Salem", "Tamil Nadu", 11.6643, 78.1460

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
    for article in articles:
        if getattr(article, 'cover_image_url', None):
            article.fallback_image = article.cover_image_url
        elif article.cover_image:
            article.fallback_image = article.cover_image.url
        else:
            cat_name = article.category.name if article.category else category_name
            article.fallback_image = get_fallback_image(cat_name, article.id)
    return articles


def index_view(request):
    date_str = datetime.now().strftime("%B %d, %Y")
    city, region, lat, lon = get_user_location(request)
    location_str = f"{city}, {region}"
    temp_f, weather_desc = get_weather_data(latitude=lat, longitude=lon)

    # Hero Articles
    hero_qs = NewsArticle.objects.all().order_by('-published_date')[:4]
    hero_list = []
    for article in hero_qs:
        cat_name = article.category.name if article.category else "default"
        hero_list.append({
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "content": article.content,
            "location": "Global",
            "date": article.published_date.strftime('%B %d, %Y'),
            "image": getattr(article, 'cover_image_url', None) or (article.cover_image.url if article.cover_image else get_fallback_image(cat_name, article.id))
        })

    # Build sections dynamically based on database categories
    sections = []
    
    # User's prioritized categories
    priority_order = [
        "World", "US politics", "UK", "Climate crisis", "Middle East", 
        "Ukraine", "Environment", "Science", "Global development", 
        "Football", "Tech", "Business", "Obituaries", "Iran-Israel war"
    ]
    
    # Assign specific layouts to ensure data density
    # Fast moving/compact topics
    compact_topics = ["Ukraine", "Iran-Israel war", "Middle East", "Science"]
    
    layouts_pool = ["grid-three-col", "grid-masonry"]

    # First fetch all non-empty categories
    all_cats = list(Category.objects.all())
    
    # Sort categories: priority ones first (in order), then alphabetical
    def sort_key(cat):
        try:
            return priority_order.index(cat.name)
        except ValueError:
            return len(priority_order) + 1
            
    all_cats.sort(key=lambda c: (sort_key(c), c.name))
    
    for idx, cat in enumerate(all_cats):
        limit = 5 if cat.name in compact_topics else 6
        articles = _annotate_articles(
            NewsArticle.objects.filter(category=cat).order_by('-published_date')[:limit],
            cat.name
        )
        if articles:
            # Decide layout
            if cat.name in compact_topics:
                layout = "grid-compact-list"
            else:
                layout = layouts_pool[idx % len(layouts_pool)]
                
            sections.append({
                "title": cat.name,
                "slug": slugify(cat.name),
                "articles": articles,
                "layout": layout,
                "accent": "#ffffff",
            })

    # Local News Injection
    local_cat_name = f"Local News - {city}"
    local_cat, _ = Category.objects.get_or_create(name=local_cat_name)
    local_articles = NewsArticle.objects.filter(category=local_cat).order_by('-published_date')[:5]
    
    if not local_articles.exists():
        import threading
        from .breaking_news_task import generate_local_news
        threading.Thread(target=generate_local_news, args=(city, region, local_cat)).start()
        
    local_annotated = _annotate_articles(local_articles, "Local News")
    if local_annotated:
        sections.insert(0, {
            "title": local_cat_name,
            "slug": slugify(local_cat_name),
            "articles": local_annotated,
            "layout": "grid-compact-list",
            "accent": "#ff9900",
        })

    # Fetch personalized articles for logged-in users
    personalized_articles = []
    if request.user.is_authenticated:
        from news.models import PersonalizedArticle
        personalized_articles = PersonalizedArticle.objects.filter(
            owner=request.user, 
            is_archived=False
        ).order_by('-created_at')[:5]

    # Trending Articles for Sidebar (Mock based on recent articles for now, or use views if tracked)
    trending_articles = NewsArticle.objects.order_by('?')[:5]

    context = {
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': location_str,
        'hero_data': hero_list,
        'hero_articles': hero_qs,
        'sections': sections,
        'personalized_articles': personalized_articles,
        'trending_articles': trending_articles,
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
    # Parse content
    paragraphs = [p.strip() for p in article.content.split('\n') if p.strip()]
    if len(paragraphs) <= 1:
        paragraphs = [article.content]

    # Similar Articles
    if article.category:
        similar_qs = NewsArticle.objects.filter(category=article.category).exclude(id=article.id).order_by('-published_date')[:3]
        similar_articles = _annotate_articles(similar_qs, cat_name)
    else:
        similar_articles = []

    # Weather/date for base template
    from datetime import datetime
    date_str = datetime.now().strftime("%B %d, %Y")
    city, region, lat, lon = get_user_location(request)
    location_str = f"{city}, {region}"
    temp_f, weather_desc = get_weather_data(latitude=lat, longitude=lon)

    context = {
        'article': article,
        'fallback_image': fallback_image,
        'paragraphs': paragraphs,
        'similar_articles': similar_articles,
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': location_str,
    }
    return render(request, 'article.html', context)


def category_view(request, category_slug):
    # Dynamically find the category matching the slug
    section_cat = None
    for cat in Category.objects.all():
        if slugify(cat.name) == category_slug:
            section_cat = cat
            break

    if section_cat is None:
        raise Http404("Category not found")

    # Fetch up to 20 articles for this category
    articles = _annotate_articles(
        NewsArticle.objects.filter(
            category=section_cat
        ).order_by('-published_date')[:20],
        section_cat.name
    )

    # Weather/date for base template
    date_str = datetime.now().strftime("%B %d, %Y")
    city, region, lat, lon = get_user_location(request)
    location_str = f"{city}, {region}"
    temp_f, weather_desc = get_weather_data(latitude=lat, longitude=lon)

    context = {
        'category_name': section_cat.name,
        'accent_color': "#ffffff",
        'active_category_slug': category_slug,
        'articles': articles,
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': location_str,
    }
    return render(request, 'category.html', context)

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from users.models import UserInteraction, UserTagScore

@login_required
@require_POST
def article_interact_view(request, article_id):
    try:
        data = json.loads(request.body)
        action = data.get('action') # "LIKE" or "DISLIKE"
        
        if action not in ["LIKE", "DISLIKE"]:
            return JsonResponse({"error": "Invalid action"}, status=400)
            
        article = get_object_or_404(NewsArticle, id=article_id)
        interaction_type = "LIKED" if action == "LIKE" else "DISLIKED"
        
        # Check if they already liked/disliked
        existing = UserInteraction.objects.filter(
            user=request.user, 
            article=article, 
            interaction_type__in=['LIKED', 'DISLIKED']
        ).first()
        
        if existing:
            if existing.interaction_type == interaction_type:
                # Toggle off
                existing.delete()
                return JsonResponse({"status": "removed", "action": action})
            else:
                # Switch vote
                existing.interaction_type = interaction_type
                existing.save()
        else:
            UserInteraction.objects.create(
                user=request.user, article=article, interaction_type=interaction_type
            )
            
        # Update tag scores
        UserTagScore.bump_for_article(request.user, article, interaction_type)
        return JsonResponse({"status": "added", "action": action})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
