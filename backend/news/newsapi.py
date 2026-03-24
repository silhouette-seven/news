import requests
import json
from django.conf import settings

def fetch_and_extend_news(query=None, category=None, count=5):
    """
    Fetches real news from NewsAPI.org (either by category or query) and
    expands the snippet into a full article using Gemini.
    """
    newsapi_key = getattr(settings, 'NEWSAPI_KEY', '92fe0acbccb84838a00e1a7d9584040a')
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    
    if not gemini_key:
        print("GEMINI_API_KEY not found in settings.")
        return []

    # 1. Fetch from NewsAPI
    if query:
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize={count}&apiKey={newsapi_key}"
    else:
        # Default to top headlines
        cat_param = f"&category={category}" if category else ""
        url = f"https://newsapi.org/v2/top-headlines?language=en{cat_param}&pageSize={count}&apiKey={newsapi_key}"

    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        print(f"NewsAPI Error: {resp.text}")
        return []
    
    data = resp.json()
    articles = data.get('articles', [])
    if not articles:
        return []

    # 2. Prepare data for Gemini
    news_items = []
    for art in articles:
        title = art.get('title')
        desc = art.get('description')
        content = art.get('content')
        
        if not title: continue
        
        # Prefer description, fallback to snippet of content, fallback to title
        text_basis = desc if desc else (content if content else title)
        
        news_items.append({
            'original_title': title,
            'original_desc': text_basis,
            'source_url': art.get('url', ''),
            'cover_image_url': art.get('urlToImage', ''),
            'author': art.get('author', 'Unknown')
        })

    if not news_items:
        return []

    # 3. Extend with Gemini
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    
    # We will ask Gemini to process a JSON array of inputs and return a JSON array of outputs
    input_json_str = json.dumps([{'title': item['original_title'], 'description': item['original_desc']} for item in news_items], ensure_ascii=False)
    
    sys_prompt = (
        "You are an expert AI journalist for 'Geo-News'. You are provided with a JSON array containing real, recent news headlines and brief descriptions.\n"
        "For each item, write a highly detailed, engaging news article (AT LEAST 200 WORDS) formatted in paragraphs separated by double newlines. "
        "Expand upon the provided facts professionally without hallucinating completely unrelated events. Use journalistic tone and structure.\n"
        "Return the output STRICTLY as a JSON array of objects, with NO markdown codeblocks. The output array MUST have the exact same length and order as the input array.\n"
        "Each output object must have the following keys:\n"
        "1. 'title': The headline (you can refine the original headline or keep it).\n"
        "2. 'summary': A 1-2 sentence compelling summary of the news.\n"
        "3. 'content': The full extended article body (>= 200 words).\n"
        f"Input Data:\n{input_json_str}"
    )

    payload = {
        "contents": [{"parts": [{"text": sys_prompt}]}]
    }

    try:
        g_resp = requests.post(gemini_url, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=60)
        g_resp.raise_for_status()
        g_data = g_resp.json()
        
        raw_text = g_data['candidates'][0]['content']['parts'][0]['text'].strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.startswith("```"): raw_text = raw_text[3:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
        
        extended_data = json.loads(raw_text.strip())
        
        # Merge back with source_url and cover_image
        final_articles = []
        for i, ext in enumerate(extended_data):
            if i < len(news_items):
                final_articles.append({
                    'title': ext.get('title', news_items[i]['original_title']),
                    'summary': ext.get('summary', news_items[i]['original_desc']),
                    'content': ext.get('content', ''),
                    'source_url': news_items[i]['source_url'],
                    'cover_image_url': news_items[i]['cover_image_url']
                })
        return final_articles

    except requests.exceptions.HTTPError as he:
        print(f"Gemini API Error: {he}")
        if he.response.status_code == 429:
            print("Rate limit reached. Falling back to native NewsAPI content to avoid breaking pipeline.")
            final_articles = []
            for item in news_items:
                fallback_content = (item['original_desc'] or "") + "\n\n" + "[Content intentionally brief due to API rate limits. Expanded coverage pending.]"
                final_articles.append({
                    'title': item['original_title'],
                    'summary': item['original_desc'][:100] + "...",
                    'content': fallback_content,
                    'source_url': item['source_url'],
                    'cover_image_url': item['cover_image_url']
                })
            return final_articles
        return []

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return []
