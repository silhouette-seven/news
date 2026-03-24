import requests
import json
import base64
import os
import re
import time
from io import BytesIO
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.conf import settings

# Common English stopwords to filter from titles
_STOPWORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'out', 'off', 'over',
    'under', 'again', 'further', 'then', 'once', 'and', 'but', 'or',
    'nor', 'not', 'so', 'very', 'just', 'about', 'up', 'its', 'it',
    'this', 'that', 'these', 'those', 'he', 'she', 'they', 'we', 'you',
    'who', 'whom', 'which', 'what', 'where', 'when', 'why', 'how',
    'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'only', 'own', 'same', 'than', 'too',
    'new', 'first', 'last', 'says', 'after', 'amid', 'announces',
    'declares', 'hits', 'passes', 'confirms', 'signals', 'launches',
    'opinion',
}


def _extract_keywords(title, max_keywords=4):
    """Extract meaningful keywords from an article title."""
    words = re.sub(r"[^a-zA-Z0-9\s'-]", '', title).split()
    keywords = [w for w in words if w.lower() not in _STOPWORDS and len(w) >= 3]
    return keywords[:max_keywords]


def get_wikimedia_image(query, index=0):
    """
    Fetches image URLs from the Wikimedia Commons API based on a query.
    Results are cached for 24 hours to ensure fast page loads.
    """
    if not query or query == "default":
        query = "World News"
        
    cache_key = f"wikimedia_images_{query.replace(' ', '_')}"
    cached_images = cache.get(cache_key)
    
    if cached_images is None:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "piprop": "original|thumbnail",
            "pithumbsize": "600",
            "generator": "search",
            "gsrsearch": f"{query} news",
            "gsrlimit": "15"
        }
        headers = {'User-Agent': 'RedemptionNewsBot/2.0'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            cached_images = []
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                img = page_data.get("thumbnail", {}).get("source") or page_data.get("original", {}).get("source")
                if img:
                    # Filter out low-quality images (icons, logos, SVGs)
                    if any(skip in img.lower() for skip in ['.svg', 'logo', 'icon', 'flag', '20px', '30px']):
                        continue
                    cached_images.append(img)
                    
        except Exception:
            cached_images = []
            
        cache.set(cache_key, cached_images, 86400)
    
    if not cached_images:
        return _get_unsplash_fallback(query)
        
    return cached_images[index % len(cached_images)]


# ─── Unsplash Fallback System ───

# Category-to-search mapping for high-quality, relevant Unsplash images
_UNSPLASH_QUERIES = {
    'world': 'world globe international',
    'politics': 'government politics parliament',
    'us politics': 'united states capitol congress',
    'uk': 'london united kingdom',
    'technology': 'technology innovation digital',
    'tech': 'technology innovation digital',
    'science': 'science laboratory research',
    'environment': 'nature environment sustainability',
    'climate crisis': 'climate change environment earth',
    'business': 'business finance corporate',
    'finance': 'stock market finance trading',
    'sports': 'sports athletics stadium',
    'football': 'football soccer stadium',
    'entertainment': 'entertainment cinema arts',
    'middle east': 'middle east architecture cityscape',
    'ukraine': 'ukraine eastern europe',
    'obituaries': 'memorial remembrance tribute',
    'global development': 'development infrastructure construction',
}

def _get_unsplash_fallback(query):
    """Return a high-quality Unsplash image URL as a reliable fallback."""
    query_lower = query.lower().strip()
    search = _UNSPLASH_QUERIES.get(query_lower, query_lower)
    return f"https://source.unsplash.com/800x450/?{search.replace(' ', ',')}"


def get_relevant_image(title):
    """
    Fetch a relevant image for an article based on its title keywords.
    Uses Wikipedia PageImages API with title-derived search terms.
    Returns the URL string of the best matching image.
    """
    keywords = _extract_keywords(title)
    if not keywords:
        return get_wikimedia_image("World News", 0)
    
    search_query = " ".join(keywords)
    cache_key = f"relevant_img_{search_query.replace(' ', '_')[:60]}"
    cached_url = cache.get(cache_key)
    
    if cached_url is not None:
        return cached_url

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "original|thumbnail",
        "pithumbsize": "600",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrlimit": "10",
    }
    headers = {'User-Agent': 'RedemptionNewsBot/2.0'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            img = (
                page_data.get("thumbnail", {}).get("source")
                or page_data.get("original", {}).get("source")
            )
            if img:
                # Skip low-quality images
                if any(skip in img.lower() for skip in ['.svg', 'logo', 'icon', '20px', '30px']):
                    continue
                cache.set(cache_key, img, 86400)
                return img
    except Exception:
        pass

    if len(keywords) > 2:
        fallback_query = " ".join(keywords[:2])
        return get_wikimedia_image(fallback_query, 0)

    fallback = _get_unsplash_fallback(search_query)
    cache.set(cache_key, fallback, 86400)
    return fallback


# ─── Cover Image Generation (Multi-Strategy Pipeline) ───

def generate_cover_image(article):
    """
    Generate a high-quality cover image for a news article.
    
    Uses a multi-strategy pipeline:
    1. Gemini native image generation (gemini-2.0-flash with image output)
    2. Imagen 4 API (if strategy 1 fails)
    3. Wikipedia keyword-based image search (fallback)
    4. Unsplash category-based fallback (last resort)
    
    Args:
        article: A NewsArticle instance with title and summary populated.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        print("CoverImage: No GEMINI_API_KEY found.")
        _fallback_cover_image(article)
        return

    # Strategy 1: Gemini native image generation
    if _try_gemini_native_image(article, api_key):
        return
    
    # Strategy 2: Imagen 4 API
    if _try_imagen_api(article, api_key):
        return

    # Strategy 3+4: Wikipedia/Unsplash fallback
    print(f"CoverImage: AI generation unavailable, using web image search for article {article.id}")
    _fallback_cover_image(article)


def _build_image_prompt(article):
    """Build a high-quality editorial image prompt from article data."""
    category_name = article.category.name if article.category else "news"
    # Use summary to give more context for a relevant image
    context = article.summary[:150] if article.summary else article.title
    
    return (
        f"A high-quality, professional photojournalism cover image. "
        f"Topic: {article.title}. "
        f"Context: {context}. "
        f"Style: Editorial photograph, well-composed, dramatic lighting, "
        f"suitable for a major news publication. "
        f"No text overlays, no watermarks, no logos, no borders. "
        f"Photorealistic, cinematic, high resolution."
    )


def _try_gemini_native_image(article, api_key):
    """
    Strategy 1: Use Gemini 2.0 Flash with native image generation.
    This model can generate images as part of its multimodal output.
    """
    try:
        gemini_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash-exp:generateContent?key={api_key}"
        )
        
        prompt = _build_image_prompt(article)

        payload = {
            "contents": [{"parts": [{"text": f"Generate a single photorealistic cover image for this news article. {prompt}"}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"],
                "responseMimeType": "text/plain",
            }
        }

        response = requests.post(
            gemini_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        # Look for image parts in the response
        candidates = data.get('candidates', [])
        if not candidates:
            return False

        parts = candidates[0].get('content', {}).get('parts', [])
        for part in parts:
            inline_data = part.get('inlineData', {})
            if inline_data.get('mimeType', '').startswith('image/'):
                image_b64 = inline_data.get('data', '')
                if image_b64:
                    image_bytes = base64.b64decode(image_b64)
                    mime = inline_data['mimeType']
                    ext = 'png' if 'png' in mime else 'jpg'
                    filename = f"article_{article.id}_cover.{ext}"
                    
                    article.cover_image.save(
                        filename,
                        ContentFile(image_bytes),
                        save=True
                    )
                    print(f"CoverImage: [Gemini Native] Generated cover for article {article.id}")
                    return True

        return False

    except Exception as e:
        print(f"CoverImage: Gemini native failed for article {article.id} - {e}")
        return False


def _try_imagen_api(article, api_key):
    """
    Strategy 2: Use the Imagen 4 API for dedicated image generation.
    """
    try:
        prompt = _build_image_prompt(article)

        imagen_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"imagen-4.0-generate-preview-06-06:predict?key={api_key}"
        )

        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9",
            }
        }

        response = requests.post(
            imagen_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        predictions = data.get('predictions', [])
        if not predictions:
            return False

        image_b64 = predictions[0].get('bytesBase64Encoded', '')
        if not image_b64:
            return False

        image_bytes = base64.b64decode(image_b64)
        filename = f"article_{article.id}_cover.png"
        
        article.cover_image.save(
            filename,
            ContentFile(image_bytes),
            save=True
        )
        print(f"CoverImage: [Imagen 4] Generated cover for article {article.id}")
        return True

    except Exception as e:
        print(f"CoverImage: Imagen 4 failed for article {article.id} - {e}")
        return False


def _fallback_cover_image(article):
    """
    Fallback strategy: download a relevant cover image from Wikipedia or Unsplash.
    Filters out low-quality images (SVGs, icons, tiny files).
    """
    try:
        image_url = get_relevant_image(article.title)
        if not image_url:
            return

        resp = requests.get(image_url, timeout=15, headers={
            'User-Agent': 'RedemptionNewsBot/2.0'
        }, allow_redirects=True)
        resp.raise_for_status()

        # Validate it's actually an image
        content_type = resp.headers.get('Content-Type', 'image/jpeg')
        if 'svg' in content_type or 'html' in content_type:
            return
        
        # Validate minimum file size (skip tiny icons/thumbnails)
        if len(resp.content) < 5000:  # Less than 5KB is likely a placeholder
            return

        if 'png' in content_type:
            ext = 'png'
        elif 'webp' in content_type:
            ext = 'webp'
        else:
            ext = 'jpg'

        filename = f"article_{article.id}_cover.{ext}"
        article.cover_image.save(
            filename,
            ContentFile(resp.content),
            save=True
        )
        print(f"CoverImage: [Fallback] Saved web image for article {article.id}")
    except Exception as e:
        print(f"CoverImage: Fallback also failed for article {article.id} - {e}")
