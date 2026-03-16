from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from .models import User, UserProfile, UserInteraction, UserTagScore


def signin_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    context = {}
    if request.method == 'POST':
        action = request.POST.get('action')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if action == 'signin':
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                context['error_signin'] = 'Invalid username or password.'

        elif action == 'signup':
            if User.objects.filter(username=username).exists():
                context['error_signup'] = 'Username already exists.'
            else:
                user = User.objects.create_user(username=username, password=password)
                UserProfile.objects.create(user=user)
                login(request, user)
                return redirect('home')

    # Weather/date for base template
    from datetime import datetime
    from news.frontend_views import get_weather_data
    context['date_str'] = datetime.now().strftime("%B %d %Y")
    temp_f, weather_desc = get_weather_data()
    context['temp_f'] = temp_f
    context['weather_desc'] = weather_desc
    context['location_str'] = "Salem, TamilNadu"

    return render(request, 'signin.html', context)


def signout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='/signin/')
def feed_view(request):
    """
    Personalized feed: ranks articles by overlap with the user's top tags.
    Articles matching multiple high-scoring tags rank higher.
    """
    from datetime import datetime
    from news.frontend_views import get_weather_data, _annotate_articles
    from news.models import NewsArticle

    user = request.user

    # Get user's top tags
    top_tag_scores = UserTagScore.get_top_tags(user, limit=15)

    if top_tag_scores:
        # Build a weighted query: articles matching the user's preferred tags
        tag_ids = [ts.tag_id for ts in top_tag_scores]
        tag_weights = {ts.tag_id: ts.score for ts in top_tag_scores}

        # Get articles that match any of the user's top tags
        articles = (
            NewsArticle.objects
            .filter(tags__id__in=tag_ids)
            .distinct()
            .prefetch_related('tags', 'category')
            .order_by('-published_date')[:50]
        )

        # Score each article by summing the user's tag scores for matching tags
        scored_articles = []
        for article in articles:
            article_tag_ids = set(article.tags.values_list('id', flat=True))
            relevance = sum(tag_weights.get(tid, 0) for tid in article_tag_ids)
            article.relevance_score = round(relevance, 1)

            # Fallback image
            cat_name = article.category.name if article.category else "default"
            from news.frontend_views import get_fallback_image
            if article.cover_image:
                article.fallback_image = article.cover_image.url
            else:
                article.fallback_image = get_fallback_image(cat_name, article.id)

            scored_articles.append(article)

        # Sort by relevance score (highest first), then by date
        scored_articles.sort(key=lambda a: (-a.relevance_score, a.published_date))
        feed_articles = scored_articles[:20]
    else:
        feed_articles = []

    # Context for base template
    date_str = datetime.now().strftime("%B %d %Y")
    temp_f, weather_desc = get_weather_data()

    context = {
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': "Salem, TamilNadu",
        'feed_articles': feed_articles,
        'top_tag_scores': top_tag_scores,
        'has_preferences': bool(top_tag_scores),
    }
    return render(request, 'feed.html', context)
