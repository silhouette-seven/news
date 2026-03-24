import requests
import json
import random
from django.conf import settings
from .models import NewsArticle, Category, BreakingNews
from django.utils.text import slugify
from datetime import datetime

def generate_and_store_breaking_news():
    """
    Called in a background thread to generate breaking news using Gemini.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        print("BreakingNews Task: No GEMINI_API_KEY found.")
        return

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    # We want a breaking news headline and a ~200 word article.
    # Return JSON so we can easily parse title and content.
    today_str = datetime.now().strftime("%B %d, %Y")
    sys_prompt = (
        "You are an AI news editor for 'Geo-News'. Your task is to report on a REAL breaking news event You can get news from the internet "
        f"that is currently happening TODAY ({today_str}) or has very recently happened within the last 24-48 hours. "
        "You MUST only report on REAL, verifiable, recently occurred events. Do NOT report on past historical events. "
        "Base your article on actual current events that can be verified through reputable news sources. "
        "Return the output in strict JSON format with the following keys:\n"
        "1. 'headline': A short, punchy breaking news ticker text (max 100 characters).\n"
        "2. 'title': The full title of the article.\n"
        "3. 'summary': A 1-2 sentence summary of the news.\n"
        "4. 'content': A detailed article measuring at least 200 words, formatted in paragraphs separated by double newlines.\n"
        "5. 'category': The category of the news (e.g., Politics, Technology, World, Business, Science, Environment).\n"
        "6. 'source_url': A URL to the original source or a reputable news outlet covering this story.\n"
        "Do not include markdown codeblocks (like ```json), just the raw JSON object."
    )

    payload = {
        "contents": [{"parts": [{"text": sys_prompt}]}]
    }

    try:
        response = requests.post(
            gemini_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        # Parse the text response
        text_response = data['candidates'][0]['content']['parts'][0]['text']
        
        # Clean up any markdown formatting if present
        text_response = text_response.strip()
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        news_data = json.loads(text_response.strip())
        
        # Get or create category
        cat_name = news_data.get('category', 'World')
        category, _ = Category.objects.get_or_create(name=cat_name)
        
        # Create the Article
        article = NewsArticle.objects.create(
            title=news_data.get('title', news_data.get('headline', 'Breaking News')),
            summary=news_data.get('summary', ''),
            content=news_data.get('content', ''),
            category=category,
            source_url=news_data.get('source_url', '')
        )
        
        # Create BreakingNews entry
        BreakingNews.objects.create(
            text=news_data.get('headline', 'BREAKING: Major event reported.'),
            article=article
        )
        print("BreakingNews Task: Successfully generated new breaking news!")

    except Exception as e:
        print(f"BreakingNews Task: Failed to generate news - {e}")


def generate_local_news(city, region, category):
    """
    Generate handful of local news articles for a user's location via Gemini
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        print("LocalNews Task: No GEMINI_API_KEY found.")
        return

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    sys_prompt = (
        f"You are a local news reporter for 'Geo-News' covering the {city}, {region} area. "
        f"Report on 3 distinct, REAL and RECENT local news events that have actually happened in this specific city/region. "
        f"You MUST only report on real, verifiable events. Do NOT invent or fabricate any news stories. "
        f"Base your articles on actual recent events that can be verified through local news sources. "
        f"Each article MUST be at least 200 words long, formatted in paragraphs. "
        f"Return the output STRICTLY as a JSON array of objects, with NO markdown codeblocks. "
        "Each object must have the following keys:\n"
        "1. 'title': The headline of the article.\n"
        "2. 'summary': A 1-2 sentence summary of the news.\n"
        "3. 'content': The full article body (>= 200 words).\n"
    )

    payload = {
        "contents": [{"parts": [{"text": sys_prompt}]}]
    }

    try:
        response = requests.post(
            gemini_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=40
        )
        response.raise_for_status()
        data = response.json()
        
        text_response = data['candidates'][0]['content']['parts'][0]['text']
        text_response = text_response.strip()
        
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        articles_data = json.loads(text_response.strip())
        
        if not isinstance(articles_data, list):
            return

        for art_data in articles_data:
            title = art_data.get('title', 'Untitled Local News')
            summary = art_data.get('summary', '')
            content = art_data.get('content', '')
            
            if len(content) < 50:
                continue 
                
            NewsArticle.objects.create(
                title=title,
                summary=summary,
                content=content,
                category=category,
            )
            
        print(f"LocalNews Task: Generated 3 local articles for {city}.")

    except Exception as e:
        print(f"LocalNews Task: Failed - {e}")
