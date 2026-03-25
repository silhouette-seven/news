import os
import io
import json
import requests as http_requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.cache import cache

from .models import NewsArticle, ArticleAudio, DailyPodcast, Category

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

@require_GET
def get_voices(request):
    """Return available voices. Since Free tier API keys don't have voices_read permission,
    we use a hardcoded list of high-quality default ElevenLabs voices."""
    
    # Standard 11Labs default voices guaranteed to work on all tiers
    default_voices = [
        {'voice_id': 'pNInz6obpgDQGcFmaJgB', 'name': 'Adam', 'category': 'Deep & Professional (Male)'},
        {'voice_id': '21m00Tcm4TlvDq8ikWAM', 'name': 'Rachel', 'category': 'Calm & Professional (Female)'},
        {'voice_id': 'ErXwobaYiN019PkySvjV', 'name': 'Antoni', 'category': 'Well-rounded (Male)'},
        {'voice_id': 'EXAVITQu4vr4xnSDxMaL', 'name': 'Sarah', 'category': 'Expressive (Female)'},
        {'voice_id': 'VR6AewLTigWG4xSOukaG', 'name': 'Arnold', 'category': 'Crisp (Male)'},
        {'voice_id': 'ThT5KcBeYPX1UaluqPye', 'name': 'Dorothy', 'category': 'Pleasant (Female)'},
        {'voice_id': 'TX3OmfUUyVNfacY16Bnc', 'name': 'Liam', 'category': 'Articulate (Male)'},
        {'voice_id': 'LcfcDJNUP1GQjkvn1xUw', 'name': 'Emily', 'category': 'Conversational (Female)'},
    ]
    
    return JsonResponse({'voices': default_voices})


@require_POST
def generate_article_audio(request, article_id):
    """Generate or retrieve TTS audio for an article."""
    try:
        body = json.loads(request.body)
        voice_id = body.get('voice_id')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    if not voice_id:
        return JsonResponse({'error': 'voice_id is required'}, status=400)

    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        return JsonResponse({'error': 'ElevenLabs API key not configured'}, status=500)

    article = get_object_or_404(NewsArticle, id=article_id)

    # 1. Check if we already generated this exact audio
    cached_audio = ArticleAudio.objects.filter(article=article, voice_id=voice_id).first()
    if cached_audio and cached_audio.audio_file:
        return JsonResponse({
            'status': 'cached',
            'audio_url': cached_audio.audio_file.url,
            'alignment': cached_audio.alignment_json
        })

    # 2. Prepare text (Headline + Summary + Content)
    text_to_read = f"{article.title}. \n\n{article.summary}\n\n{article.content}"
    # ElevenLabs has limits per request, typically 5000 chars is safe for standard tier.
    # Truncate if necessary to avoid API errors
    text_to_read = text_to_read[:4500] 

    # 3. Call ElevenLabs API
    headers = {
        "Accept": "application/json", # Changed to accept json for timestamps
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text_to_read,
        "model_id": "eleven_flash_v2_5", # Fast, low latency model
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        # Append /with-timestamps to get alignment data
        tts_url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}/with-timestamps"
        response = http_requests.post(tts_url, json=data, headers=headers, timeout=20)
        response.raise_for_status()
        
        resp_data = response.json()
        import base64
        audio_content = base64.b64decode(resp_data.get('audio_base64', ''))
        alignment = resp_data.get('alignment', {})
        
        # 4. Save audio and alignment to model
        filename = f"article_{article.id}_{voice_id}.mp3"
        
        article_audio = ArticleAudio.objects.create(
            article=article,
            voice_id=voice_id,
            alignment_json=alignment
        )
        article_audio.audio_file.save(filename, ContentFile(audio_content))
        
        return JsonResponse({
            'status': 'generated',
            'audio_url': article_audio.audio_file.url,
            'alignment': alignment
        })
        
    except Exception as e:
        return JsonResponse({'error': f'ElevenLabs generation failed: {str(e)}'}, status=500)


@login_required
@require_POST
def generate_daily_podcast(request):
    """Generate a 3-minute personalized podcast (Limit 1 per day)."""
    user = request.user
    today = timezone.localdate()
    
    # 1. Check limit
    existing = DailyPodcast.objects.filter(user=user, date=today).first()
    if existing and existing.audio_file:
        return JsonResponse({
            'status': 'cached',
            'audio_url': existing.audio_file.url,
            'script': existing.script
        })
        
    gemini_key = settings.GEMINI_API_KEY
    eleven_key = settings.ELEVENLABS_API_KEY
    if not gemini_key or not eleven_key:
        return JsonResponse({'error': 'API keys not fully configured'}, status=500)
        
    try:
        body = json.loads(request.body)
        voice_id = body.get('voice_id', '21m00Tcm4TlvDq8ikWAM') # Rachel (default)
    except:
        voice_id = '21m00Tcm4TlvDq8ikWAM'

    # 2. Gather context for script
    # Get user's preferred tags or top interactions
    target_topics = "General World News"
    if hasattr(user, 'profile') and user.profile.preferred_tags.exists():
        tags = list(user.profile.preferred_tags.values_list('name', flat=True))
        target_topics = ', '.join(tags)

    # Get recent breaking news
    from .models import BreakingNews
    breaking_qs = BreakingNews.objects.order_by('-created_at')[:3]
    breaking_text = " ".join([b.text for b in breaking_qs]) if breaking_qs else "No major breaking news today."

    # 3. Ask Gemini to write a 3-minute broadcast script (~450 words)
    system_prompt = (
        f"You are the host of a daily 3-minute personalized news podcast for a listener named {user.username}. "
        f"Their interests are: {target_topics}. "
        f"Recent breaking news: {breaking_text}. "
        f"Write a continuous, engaging, conversational radio broadcast script covering their interests and the breaking news. "
        f"It MUST NOT be longer than 450 words. Do not include sound effects brackets or host directions, JUST the spoken words. "
        f"Start with a warm welcome."
    )
    
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    resp = http_requests.post(
        gemini_url,
        json={"contents": [{"parts": [{"text": system_prompt}]}]},
        timeout=30,
    )
    resp.raise_for_status()
    gemini_data = resp.json()
    script = gemini_data['candidates'][0]['content']['parts'][0]['text'].strip()
    
    # 4. Send script to ElevenLabs
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": eleven_key
    }
    
    data = {
        "text": script,
        "model_id": "eleven_multilingual_v2", # Better for longer form
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    tts_url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
    tts_resp = http_requests.post(tts_url, json=data, headers=headers, timeout=60)
    tts_resp.raise_for_status()
    
    # 5. Save podcast
    filename = f"podcast_{user.id}_{today.strftime('%Y%m%d')}.mp3"
    podcast = DailyPodcast.objects.create(
        user=user,
        script=script
    )
    podcast.audio_file.save(filename, ContentFile(tts_resp.content))
    
    return JsonResponse({
        'status': 'generated',
        'audio_url': podcast.audio_file.url,
        'script': script
    })


@login_required
@require_POST
def generate_daily_article(request):
    """
    Generate a personalized daily article (200-300 words) based on user interests.
    Uses the newsapi pipeline to fetch relevant news, then condenses into one article.
    Saves cover images from source news for display. Limited to 1 per day per user.
    """
    from .models import PersonalizedArticle, Tag
    from .newsapi import fetch_and_extend_news
    from news.frontend_views import get_fallback_image
    from users.models import UserTagScore

    user = request.user
    today = timezone.localdate()

    # 1. Check if article already exists for today
    existing = PersonalizedArticle.objects.filter(
        owner=user,
        generated_date=today,
        is_archived=False,
        topic__startswith='Daily Briefing'
    ).first()

    if existing:
        return JsonResponse({
            'status': 'cached',
            'article_url': f'/article/ai/{existing.id}/',
            'title': existing.title,
        })

    # 2. Determine user interests
    top_tag_scores = UserTagScore.get_top_tags(user, limit=5)
    if top_tag_scores:
        interests = ", ".join([ts.tag.name for ts in top_tag_scores])
    else:
        interests = "entertainment, sports, technology"

    # 3. Fetch news using newsapi pipeline
    try:
        articles_data = fetch_and_extend_news(query=interests, count=3)
    except Exception as fetch_err:
        print(f"DailyArticle: Fetch failed - {fetch_err}")
        articles_data = []

    if not articles_data:
        return JsonResponse({
            'error': 'Could not fetch news for your interests. The news service may be temporarily unavailable. Please try again later.'
        }, status=500)

    # 4. Collect cover images from source articles (for collage display)
    cover_images = []
    for ad in articles_data:
        img = ad.get('cover_image_url', '')
        if img and img.strip():
            cover_images.append(img.strip())

    # Use first available as primary cover, store all for potential collage
    primary_cover = cover_images[0] if cover_images else get_fallback_image('Daily Briefing', user.id)

    # 5. Condense the fetched articles into a single 200-300 word article
    gemini_key = settings.GEMINI_API_KEY
    if not gemini_key:
        return JsonResponse({'error': 'AI service not configured.'}, status=500)

    # Build rich context for Gemini from the pipeline articles
    article_contexts = []
    for i, ad in enumerate(articles_data):
        article_contexts.append(
            f"Article {i+1}:\n"
            f"Title: {ad.get('title', '')}\n"
            f"Summary: {ad.get('summary', '')}\n"
            f"Content excerpt: {ad.get('content', '')[:300]}"
        )
    context_text = "\n\n".join(article_contexts)

    condense_prompt = (
        f"You are a personal news editor for 'Geo-News'. The reader is interested in: {interests}.\n"
        f"Below are full news articles from today that match their interests:\n\n{context_text}\n\n"
        f"Write a single, cohesive personalized daily briefing article (200-300 words) that:\n"
        f"- Covers the key highlights from ALL the stories above\n"
        f"- Uses an engaging journalistic tone with clear paragraphs\n"
        f"- Has a compelling, specific headline (not generic like 'Daily Briefing')\n"
        f"- Feels like a professional news article, not a summary list\n\n"
        f"Return STRICTLY a JSON object with NO markdown codeblocks:\n"
        f'{{"title": "compelling headline", "summary": "1-2 sentence hook", "content": "200-300 word article body with paragraphs separated by double newlines"}}'
    )

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"

    try:
        resp = http_requests.post(
            gemini_url,
            json={"contents": [{"parts": [{"text": condense_prompt}]}]},
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data['candidates'][0]['content']['parts'][0]['text'].strip()

        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.startswith("```"): raw_text = raw_text[3:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]

        result = json.loads(raw_text.strip())

        # 6. Save as PersonalizedArticle (private to the user)
        pa = PersonalizedArticle.objects.create(
            owner=user,
            title=result.get('title', 'Your Daily Briefing'),
            summary=result.get('summary', ''),
            content=result.get('content', ''),
            topic=f"Daily Briefing - {interests[:80]}",
            cover_image_url=primary_cover,
            generated_date=today,
        )

        # Attach tags from source articles
        all_tags = set()
        for ad in articles_data:
            for t in ad.get('tags', [])[:3]:
                t_name = str(t).strip()[:50]
                if t_name:
                    all_tags.add(t_name)
        for t_name in list(all_tags)[:5]:
            tag_obj, _ = Tag.objects.get_or_create(name=t_name)
            pa.tags.add(tag_obj)

        return JsonResponse({
            'status': 'generated',
            'article_url': f'/article/ai/{pa.id}/',
            'title': pa.title,
        })

    except http_requests.exceptions.HTTPError as he:
        error_msg = f'API error: {he}'
        if hasattr(he, 'response') and he.response.status_code == 429:
            error_msg = 'AI service rate limit reached. Please try again in a minute.'
        print(f"DailyArticle: Gemini error - {error_msg}")
        return JsonResponse({'error': error_msg}, status=500)

    except Exception as e:
        print(f"DailyArticle: Unexpected error - {e}")
        return JsonResponse({'error': f'Article generation failed: {str(e)}'}, status=500)


