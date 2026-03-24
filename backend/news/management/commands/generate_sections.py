import requests
import json
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from news.models import NewsArticle, Category
from datetime import datetime

class Command(BaseCommand):
    help = 'Generates 3 articles each for the specified layout categories using NewsAPI and Gemini API'

    def handle(self, *args, **kwargs):
        from news.newsapi import fetch_and_extend_news
        
        priority_order = [
            "World", "US politics", "Tech", "Climate crisis", "Middle East", 
            "Environment", "Science", "Business", "Football", "Global development"
        ]

        self.stdout.write(f"Starting generation for {len(priority_order)} categories...")

        for category_name in priority_order:
            self.stdout.write(self.style.WARNING(f"\nGenerating articles for {category_name}..."))
            
            # Create or get category
            category, _ = Category.objects.get_or_create(name=category_name)

            try:
                # Use query-based search for topics not in standard NewsAPI categories
                standard_cats = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
                cat_lower = category_name.lower().split(" ")[0]
                
                if cat_lower in standard_cats:
                    articles_data = fetch_and_extend_news(category=cat_lower, count=3)
                else:
                    articles_data = fetch_and_extend_news(query=category_name, count=3)
                
                if not articles_data:
                    self.stdout.write(self.style.ERROR(f"No articles returned for {category_name}"))
                    continue

                for art_data in articles_data:
                    title = art_data.get('title', 'Untitled')
                    summary = art_data.get('summary', '')
                    content = art_data.get('content', '')
                    
                    if len(content) < 50:
                        continue # Skip bad generations
                        
                    article = NewsArticle.objects.create(
                        title=title,
                        summary=summary,
                        content=content,
                        category=category,
                        source_url=art_data.get('source_url', ''),
                    )
                    
                    # Download and save image
                    img_url = art_data.get('cover_image_url')
                    if img_url:
                        try:
                            import requests
                            from django.core.files.base import ContentFile
                            r = requests.get(img_url, timeout=5)
                            if r.status_code == 200:
                                ext = 'jpg'
                                if '.png' in img_url.lower(): ext = 'png'
                                article.cover_image.save(f"gen_cover_{article.id}.{ext}", ContentFile(r.content), save=True)
                        except Exception as e:
                            pass
                    
                self.stdout.write(self.style.SUCCESS(f"Successfully generated {len(articles_data)} articles for {category_name}."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed category {category_name}: {str(e)}"))
                
            self.stdout.write(self.style.WARNING(f"Sleeping for 25 seconds to respect Gemini 15 RPM limits..."))
            time.sleep(25)
            
        self.stdout.write(self.style.SUCCESS("\nAll specified categories generated successfully!"))
