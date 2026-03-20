import requests
from django.core.cache import cache

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

import re

def _extract_keywords(title, max_keywords=4):
    """Extract meaningful keywords from an article title."""
    # Remove special characters and split
    words = re.sub(r"[^a-zA-Z0-9\s'-]", '', title).split()
    # Filter stopwords, keep words with 3+ characters
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
        headers = {'User-Agent': 'AntigravityNewsBot/1.0'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            cached_images = []
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                img = page_data.get("thumbnail", {}).get("source") or page_data.get("original", {}).get("source")
                if img:
                    cached_images.append(img)
                    
        except Exception:
            cached_images = []
            
        # Cache the results for 24 hours (86400 seconds)
        cache.set(cache_key, cached_images, 86400)
    
    if not cached_images:
        # Fallback if API fails or yields no valid results
        return "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=600&auto=format&fit=crop"
        
    return cached_images[index % len(cached_images)]


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
    headers = {'User-Agent': 'AntigravityNewsBot/1.0'}

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
                cache.set(cache_key, img, 86400)
                return img
    except Exception:
        pass

    # Fallback: try with just first two keywords
    if len(keywords) > 2:
        fallback_query = " ".join(keywords[:2])
        return get_wikimedia_image(fallback_query, 0)

    fallback = "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=600&auto=format&fit=crop"
    cache.set(cache_key, fallback, 86400)
    return fallback

