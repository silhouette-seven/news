import requests
import json
import random
from django.conf import settings
from .models import NewsArticle, Category, BreakingNews
from django.utils.text import slugify
from datetime import datetime

def generate_and_store_breaking_news(country='in'):
    """
    Called in a background thread to generate breaking news using the newsapi pipeline.
    Uses the user's country for relevant headlines.
    """
    from .newsapi import fetch_and_extend_news
    articles_data = fetch_and_extend_news(category='general', country=country, count=1)
    if not articles_data:
        print("BreakingNews Task: Failed to generate news via newsapi.")
        return

    news_data = articles_data[0]
    
    # Use the category detected by the pipeline instead of hardcoding 'World'
    category_name = news_data.get('category', 'World')
    category, _ = Category.objects.get_or_create(name=category_name)
    
    # Create the Article
    article = NewsArticle.objects.create(
        title=news_data.get('title', 'Breaking News'),
        summary=news_data.get('summary', ''),
        content=news_data.get('content', ''),
        category=category,
        source_url=news_data.get('source_url', ''),
        cover_image_url=news_data.get('cover_image_url', ''),
    )
    
    # Attach tags
    from .models import Tag
    for t_name in news_data.get('tags', [])[:3]:
        t_name = str(t_name).strip()[:50]
        if t_name:
            tag_obj, _ = Tag.objects.get_or_create(name=t_name)
            article.tags.add(tag_obj)
    
    BreakingNews.objects.create(
        text="BREAKING: " + news_data.get('title', 'Major event reported.'),
        article=article
    )
    print(f"BreakingNews Task: Successfully generated breaking news in category '{category_name}'!")


def generate_local_news(city, region, category):
    """
    Generate handful of local news articles for a user's location via newsapi
    """
    from .newsapi import fetch_and_extend_news
    query = f"{city} {region} local news"
    articles_data = fetch_and_extend_news(query=query, count=3)
    if not articles_data:
        print(f"LocalNews Task: No articles generated for {city}, {region}.")
        return

    from .models import Tag
    for art_data in articles_data:
        title = art_data.get('title', 'Untitled Local News')
        summary = art_data.get('summary', '')
        content = art_data.get('content', '')
        
        if len(content) < 50:
            continue
            
        article = NewsArticle.objects.create(
            title=title,
            summary=summary,
            content=content,
            category=category,
            source_url=art_data.get('source_url', ''),
            cover_image_url=art_data.get('cover_image_url', ''),
        )
        
        # Attach tags
        for t_name in art_data.get('tags', [])[:3]:
            t_name = str(t_name).strip()[:50]
            if t_name:
                tag_obj, _ = Tag.objects.get_or_create(name=t_name)
                article.tags.add(tag_obj)

    print(f"LocalNews Task: Generated local articles for {city}.")
