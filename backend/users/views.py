from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .models import User, UserProfile, UserInteraction, UserTagScore
import json


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
    Personalized feed: shows general recommended articles and custom AI-generated articles.
    """
    from datetime import datetime
    from django.utils import timezone
    from news.frontend_views import get_weather_data, _annotate_articles
    from news.models import NewsArticle, PersonalizedArticle
    from users.models import UserTagScore

    user = request.user
    today = timezone.now().date()
    
    # Check if AI articles were generated today
    has_generated_today = PersonalizedArticle.objects.filter(owner=user, generated_date=today).exists()
    auto_generate = not has_generated_today

    # Fetch active personalized articles
    personalized_articles = PersonalizedArticle.objects.filter(owner=user, is_archived=False).order_by('-created_at')

    # Get user's top tags for general recommendations
    top_tag_scores = UserTagScore.get_top_tags(user, limit=15)
    top_tags_str = ", ".join([ts.tag.name for ts in top_tag_scores[:5]]) if top_tag_scores else "Latest News"

    if top_tag_scores:
        # Build a weighted query: articles matching the user's preferred tags or categories
        top_tag_names = [ts.tag.name for ts in top_tag_scores]
        tag_weights = {ts.tag.name: ts.score for ts in top_tag_scores}

        # Get articles that match any of the user's top tags OR categories
        articles = (
            NewsArticle.objects
            .filter(Q(tags__name__in=top_tag_names) | Q(category__name__in=top_tag_names))
            .distinct()
            .prefetch_related('tags', 'category')
            .order_by('-published_date')[:50]
        )

        # Score each article by summing the user's tag scores for matching tags
        scored_articles = []
        for article in articles:
            article_tag_names = set(article.tags.values_list('name', flat=True))
            if article.category:
                article_tag_names.add(article.category.name)
                
            relevance = sum(tag_weights.get(name, 0) for name in article_tag_names)
            article.relevance_score = round(relevance, 1)

            # Fallback image
            cat_name = article.category.name if article.category else "default"
            from news.frontend_views import get_fallback_image
            if article.cover_image:
                article.fallback_image = article.cover_image.url
            else:
                article.fallback_image = get_fallback_image(cat_name, article.id)

            scored_articles.append(article)

        # Sort by relevance score (highest first), then by date (newest first)
        scored_articles.sort(key=lambda a: (-a.relevance_score, -a.published_date.timestamp()))
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
        'personalized_articles': personalized_articles,
        'auto_generate': auto_generate,
        'top_tags_str': top_tags_str,
    }
    return render(request, 'feed.html', context)


@login_required(login_url='/signin/')
@require_POST
def generate_personalized_articles(request):
    """AJAX endpoint: generates 5 custom articles using Gemini based on user interests."""
    from django.conf import settings
    from django.utils import timezone
    from news.models import PersonalizedArticle, Tag
    from news.frontend_views import get_fallback_image
    import requests as http_requests

    try:
        body = json.loads(request.body)
        interests = body.get('interests', '').strip()
    except Exception:
        interests = ""

    if not interests:
        from users.models import UserTagScore
        top_tag_scores = UserTagScore.get_top_tags(request.user, limit=5)
        interests = ", ".join([ts.tag.name for ts in top_tag_scores]) if top_tag_scores else "World News"
    else:
        # User defined explicit interests, save them to profile by boosting score
        from users.models import UserTagScore
        from news.models import Tag
        explicit_tags = [t.strip() for t in interests.split(',') if t.strip()]
        for t_name in explicit_tags:
            tag_obj, _ = Tag.objects.get_or_create(name=t_name[:50])
            uts, _ = UserTagScore.objects.get_or_create(user=request.user, tag=tag_obj)
            uts.score += 20.0  # Boost for explicit generation usage
            uts.save()

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({'error': 'AI service is not configured.'}, status=500)

    # Auto-archive old personalized articles for this user
    PersonalizedArticle.objects.filter(owner=request.user, is_archived=False).update(is_archived=True)

    system_prompt = (
        f"You are a cutting-edge AI news desk. Your task is to write exactly 5 unique, completely formatted news articles "
        f"tailored to the following user interests: {interests}.\n\n"
        f"Each article MUST be at least 200 words, highly detailed, engaging, and structured logically. "
        f"Return the output STRICTLY as a valid JSON list of objects. Do not include markdown blocks like ```json "
        f"or any text outside of the JSON array.\n\n"
        f"Format of the JSON list:\n"
        f"[\n"
        f"  {{\n"
        f"    \"title\": \"Compelling Article Headline\",\n"
        f"    \"topic\": \"Category/Topic\",\n"
        f"    \"summary\": \"A sharp 2-3 sentence summary...\",\n"
        f"    \"content\": \"Full article text with paragraphs separated by exactly one newline. At least 200 words...\",\n"
        f"    \"tags\": [\"Tag1\", \"Tag2\", \"Tag3\"]\n"
        f"  }},\n"
        f"  ... (4 more objects)\n"
        f"]"
    )

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    try:
        resp = http_requests.post(
            gemini_url,
            json={"contents": [{"parts": [{"text": system_prompt}]}]},
            timeout=50,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Strip markdown json blocks if returned
        if raw_text.startswith('```json'): raw_text = raw_text[7:]
        elif raw_text.startswith('```'): raw_text = raw_text[3:]
        if raw_text.endswith('```'): raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        articles_data = json.loads(raw_text)
        
        created = []
        today = timezone.now().date()
        for i, ad in enumerate(articles_data):
            # Use fixed fallback images safely mapped to topics instead of Unsplash
            img_url = get_fallback_image(ad.get('topic', 'General'), i)
            
            pa = PersonalizedArticle.objects.create(
                owner=request.user,
                title=ad.get('title', 'Untitled'),
                summary=ad.get('summary', ''),
                content=ad.get('content', ''),
                topic=ad.get('topic', 'General'),
                cover_image_url=img_url,
                generated_date=today
            )
            
            # Save and attach tags
            tags_list = ad.get('tags', [])
            if isinstance(tags_list, list):
                for t_name in tags_list[:3]:
                    t_name = str(t_name).strip()
                    if t_name:
                        tag_obj, _ = Tag.objects.get_or_create(name=t_name[:50])
                        pa.tags.add(tag_obj)
                        
            created.append({
                'id': pa.id,
                'title': pa.title,
                'summary': pa.summary,
                'topic': pa.topic,
                'date': pa.created_at.strftime('%b %d, %Y'),
                'image': img_url,
                'url': f"/article/ai/{pa.id}/"
            })
            
        return JsonResponse({'articles': created})

    except Exception as e:
        return JsonResponse({'error': f'AI Generation failed: {str(e)}'}, status=500)


@login_required(login_url='/signin/')
def personalized_article_detail_view(request, article_id):
    from django.shortcuts import get_object_or_404, render
    from news.models import PersonalizedArticle
    from news.frontend_views import get_weather_data
    from datetime import datetime

    article = get_object_or_404(PersonalizedArticle, id=article_id, owner=request.user)
    temp_f, weather_desc = get_weather_data()
    date_str = datetime.now().strftime("%B %d %Y")

    context = {
        'article': article,
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': "Salem, TamilNadu",
        'is_personalized': True,
    }
    return render(request, 'article.html', context)

# ================================================
# AI ASSISTANT VIEWS
# ================================================

@login_required(login_url='/signin/')
def ai_assistant_view(request):
    """Render the AI Assistant page."""
    from datetime import datetime
    from news.frontend_views import get_weather_data

    date_str = datetime.now().strftime("%B %d %Y")
    temp_f, weather_desc = get_weather_data()

    context = {
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': "Salem, TamilNadu",
    }
    return render(request, 'ai_assistant.html', context)


@login_required(login_url='/signin/')
@require_GET
def ai_search_articles(request):
    """AJAX endpoint: search articles by title/summary."""
    from news.models import NewsArticle
    from news.frontend_views import get_fallback_image

    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    articles = (
        NewsArticle.objects
        .filter(Q(title__icontains=query) | Q(summary__icontains=query))
        .select_related('category')
        .order_by('-published_date')[:15]
    )

    results = []
    for i, article in enumerate(articles):
        cat_name = article.category.name if article.category else "default"
        results.append({
            'id': article.id,
            'title': article.title,
            'summary': article.summary[:150],
            'category': cat_name,
            'date': article.published_date.strftime('%b %d, %Y'),
            'image': article.cover_image.url if article.cover_image else get_fallback_image(cat_name, i),
        })

    return JsonResponse({'results': results})


@login_required(login_url='/signin/')
@require_POST
def ai_ask_gemini(request):
    """AJAX endpoint: send article + prompt to Gemini API, return response."""
    from news.models import NewsArticle
    from django.conf import settings
    import requests as http_requests

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    article_id = body.get('article_id')
    prompt = body.get('prompt', '').strip()

    if not article_id or not prompt:
        return JsonResponse({'error': 'Please select an article and enter a prompt.'}, status=400)

    try:
        article = NewsArticle.objects.get(id=article_id)
    except NewsArticle.DoesNotExist:
        return JsonResponse({'error': 'Article not found.'}, status=404)

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({'error': 'AI service is not configured.'}, status=500)

    # Build context prompt
    system_prompt = (
        f"You are a helpful news analysis assistant. The user has selected the following news article:\n\n"
        f"Title: {article.title}\n"
        f"Category: {article.category.name if article.category else 'General'}\n"
        f"Summary: {article.summary}\n"
        f"Full Content: {article.content}\n\n"
        f"The user's question about this article is: {prompt}\n\n"
        f"Provide a clear, informative, and concise response."
    )

    # Call Gemini API
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    try:
        resp = http_requests.post(
            gemini_url,
            json={
                "contents": [{"parts": [{"text": system_prompt}]}]
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        return JsonResponse({'response': text})
    except http_requests.exceptions.Timeout:
        return JsonResponse({'error': 'AI service timed out. Please try again.'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'AI service error: {str(e)}'}, status=500)


# ================================================
# PROFILE VIEW
# ================================================

@login_required(login_url='/signin/')
def profile_view(request):
    """User profile page with interests and reading history."""
    from datetime import datetime
    from news.frontend_views import get_weather_data

    user = request.user
    top_tags = UserTagScore.get_top_tags(user, limit=15)
    total_reads = UserInteraction.objects.filter(user=user, interaction_type='READ').count()
    recent_interactions = (
        UserInteraction.objects
        .filter(user=user)
        .select_related('article')
        .order_by('-timestamp')[:20]
    )

    date_str = datetime.now().strftime("%B %d %Y")
    temp_f, weather_desc = get_weather_data()
    top_tags_str = ", ".join([ts.tag.name for ts in top_tags[:5]]) if top_tags else ""

    context = {
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': "Salem, TamilNadu",
        'top_tags': top_tags,
        'top_tags_str': top_tags_str,
        'total_reads': total_reads,
        'recent_interactions': recent_interactions,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='/signin/')
@require_POST
def save_interests_view(request):
    import json
    from django.http import JsonResponse
    from users.models import UserTagScore
    from news.models import Tag
    try:
        data = json.loads(request.body)
        tags_str = data.get('tags', '')
        tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
        
        # Boost scores heavily for explicitly saved tags
        for t_name in tag_names:
            tag_obj, _ = Tag.objects.get_or_create(name=t_name[:50])
            uts, _ = UserTagScore.objects.get_or_create(user=request.user, tag=tag_obj)
            uts.score += 50.0  # High explicit boost
            uts.save()
            
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
