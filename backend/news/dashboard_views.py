import json
import requests as http_requests
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
from .models import NewsArticle, Category, Tag, PersonalizedArticle, BreakingNews
from users.models import User, UserInteraction


@staff_member_required(login_url='/signin/')
def dashboard_view(request):
    """Main dashboard page."""
    from datetime import datetime
    from .frontend_views import get_weather_data

    articles = NewsArticle.objects.select_related('category').order_by('-published_date')
    users = User.objects.all().order_by('-date_joined')
    categories = Category.objects.all().order_by('name')

    date_str = datetime.now().strftime("%B %d %Y")
    temp_f, weather_desc = get_weather_data()

    context = {
        'articles': articles,
        'users': users,
        'categories': categories,
        'date_str': date_str,
        'temp_f': temp_f,
        'weather_desc': weather_desc,
        'location_str': 'Admin Dashboard',
        'total_articles': articles.count(),
        'total_users': users.count(),
        'total_categories': categories.count(),
    }
    return render(request, 'dashboard.html', context)


@staff_member_required(login_url='/signin/')
@require_POST
def dashboard_delete_article(request, article_id):
    """AJAX: Delete an article."""
    article = get_object_or_404(NewsArticle, id=article_id)
    # Delete cover image file if present
    if article.cover_image:
        article.cover_image.delete(save=False)
    article.delete()
    return JsonResponse({'status': 'deleted', 'id': article_id})


@staff_member_required(login_url='/signin/')
def dashboard_edit_article(request, article_id):
    """GET: return article data as JSON. POST: save edits."""
    article = get_object_or_404(NewsArticle, id=article_id)

    if request.method == 'GET':
        return JsonResponse({
            'id': article.id,
            'title': article.title,
            'summary': article.summary,
            'content': article.content,
            'category': article.category.name if article.category else '',
            'source_url': article.source_url or '',
            'tags': list(article.tags.values_list('name', flat=True)),
            'cover_image': article.cover_image.url if article.cover_image else '',
        })

    # POST — save edits
    title = request.POST.get('title', '').strip()
    summary = request.POST.get('summary', '').strip()
    content = request.POST.get('content', '').strip()
    category_name = request.POST.get('category', '').strip()
    source_url = request.POST.get('source_url', '').strip()
    tags_str = request.POST.get('tags', '').strip()

    if not title:
        return JsonResponse({'error': 'Title is required.'}, status=400)

    article.title = title
    article.summary = summary
    article.content = content
    article.source_url = source_url

    if category_name:
        cat, _ = Category.objects.get_or_create(name=category_name)
        article.category = cat

    # Handle cover image upload
    if 'cover_image' in request.FILES:
        if article.cover_image:
            article.cover_image.delete(save=False)
        article.cover_image = request.FILES['cover_image']

    # Handle cover image removal
    if request.POST.get('remove_cover_image') == 'true':
        if article.cover_image:
            article.cover_image.delete(save=False)
        article.cover_image = None

    article.save()

    # Update tags
    if tags_str:
        article.tags.clear()
        for t_name in tags_str.split(','):
            t_name = t_name.strip()[:50]
            if t_name:
                tag_obj, _ = Tag.objects.get_or_create(name=t_name)
                article.tags.add(tag_obj)

    return JsonResponse({'status': 'saved', 'id': article.id})


@staff_member_required(login_url='/signin/')
@require_POST
def dashboard_add_article(request):
    """POST: Create a new article."""
    title = request.POST.get('title', '').strip()
    summary = request.POST.get('summary', '').strip()
    content = request.POST.get('content', '').strip()
    category_name = request.POST.get('category', '').strip()
    source_url = request.POST.get('source_url', '').strip()
    tags_str = request.POST.get('tags', '').strip()

    if not title:
        return JsonResponse({'error': 'Title is required.'}, status=400)

    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(name=category_name)

    article = NewsArticle.objects.create(
        title=title,
        summary=summary,
        content=content,
        category=category,
        source_url=source_url,
    )

    if 'cover_image' in request.FILES:
        article.cover_image = request.FILES['cover_image']
        article.save()

    if tags_str:
        for t_name in tags_str.split(','):
            t_name = t_name.strip()[:50]
            if t_name:
                tag_obj, _ = Tag.objects.get_or_create(name=t_name)
                article.tags.add(tag_obj)

    return JsonResponse({'status': 'created', 'id': article.id})


@staff_member_required(login_url='/signin/')
@require_POST
def dashboard_generate_articles(request):
    """AJAX: Generate articles via Gemini using a custom prompt."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    prompt = body.get('prompt', '').strip()
    category_name = body.get('category', '').strip()
    count = min(int(body.get('count', 3)), 10)

    if not prompt:
        return JsonResponse({'error': 'Please provide a prompt.'}, status=400)

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({'error': 'AI service is not configured.'}, status=500)

    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(name=category_name)

    system_prompt = (
        f"You are a reliable AI journalist for 'Redemption News'. Based on the following editorial direction, "
        f"write exactly {count} unique news articles.\n\n"
        f"Editorial direction: {prompt}\n\n"
        f"CRITICAL: Each article MUST be based on REAL, RECENT, and VERIFIABLE news events. "
        f"Do NOT invent or fabricate any news. Only report on events that have actually happened.\n\n"
        f"Each article MUST be at least 200 words, detailed, and well-structured. "
        f"Return the output STRICTLY as a valid JSON array. No markdown codeblocks.\n\n"
        f"Each object must have:\n"
        f"- \"title\": headline\n"
        f"- \"summary\": 1-2 sentence summary\n"
        f"- \"content\": full article (>= 200 words, paragraphs separated by newlines)\n"
        f"- \"source_url\": URL to a reputable source covering this story\n"
        f"- \"tags\": [\"Tag1\", \"Tag2\", \"Tag3\"]\n"
    )

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    try:
        resp = http_requests.post(
            gemini_url,
            json={"contents": [{"parts": [{"text": system_prompt}]}]},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data['candidates'][0]['content']['parts'][0]['text'].strip()

        if raw_text.startswith('```json'):
            raw_text = raw_text[7:]
        elif raw_text.startswith('```'):
            raw_text = raw_text[3:]
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3]

        articles_data = json.loads(raw_text.strip())
        created = []

        for ad in articles_data:
            article = NewsArticle.objects.create(
                title=ad.get('title', 'Untitled'),
                summary=ad.get('summary', ''),
                content=ad.get('content', ''),
                category=category,
                source_url=ad.get('source_url', ''),
            )
            # Attach tags
            tags_list = ad.get('tags', [])
            if isinstance(tags_list, list):
                for t_name in tags_list[:5]:
                    t_name = str(t_name).strip()[:50]
                    if t_name:
                        tag_obj, _ = Tag.objects.get_or_create(name=t_name)
                        article.tags.add(tag_obj)

            created.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'category': category.name if category else 'Uncategorized',
                'date': article.published_date.strftime('%b %d, %Y'),
                'source_url': article.source_url or '',
            })

        return JsonResponse({'articles': created})

    except Exception as e:
        return JsonResponse({'error': f'AI Generation failed: {str(e)}'}, status=500)


@staff_member_required(login_url='/signin/')
@require_POST
def dashboard_refine_article(request):
    """AJAX: Send article content to Gemini to refine/polish it."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    title = body.get('title', '').strip()
    content = body.get('content', '').strip()
    instruction = body.get('instruction', 'Polish and improve this article').strip()

    if not content:
        return JsonResponse({'error': 'No content to refine.'}, status=400)

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({'error': 'AI service is not configured.'}, status=500)

    system_prompt = (
        f"You are a professional news editor. A journalist has written the following draft article.\n\n"
        f"Title: {title}\n"
        f"Content:\n{content}\n\n"
        f"The editor's instructions are: {instruction}\n\n"
        f"Provide the refined version. IMPORTANT: The article must remain factually accurate and grounded in reality. "
        f"Do NOT add fictional information. Only improve clarity, structure, grammar, and flow.\n\n"
        f"Return ONLY a JSON object with these keys:\n"
        f"- \"title\": refined title\n"
        f"- \"summary\": a sharp 1-2 sentence summary\n"
        f"- \"content\": the refined full article text"
    )

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    try:
        resp = http_requests.post(
            gemini_url,
            json={"contents": [{"parts": [{"text": system_prompt}]}]},
            timeout=40,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data['candidates'][0]['content']['parts'][0]['text'].strip()

        if raw_text.startswith('```json'):
            raw_text = raw_text[7:]
        elif raw_text.startswith('```'):
            raw_text = raw_text[3:]
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3]

        result = json.loads(raw_text.strip())
        return JsonResponse({
            'title': result.get('title', title),
            'summary': result.get('summary', ''),
            'content': result.get('content', content),
        })

    except Exception as e:
        return JsonResponse({'error': f'AI Refinement failed: {str(e)}'}, status=500)
