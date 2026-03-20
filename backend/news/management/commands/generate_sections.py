import requests
import json
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from news.models import NewsArticle, Category

class Command(BaseCommand):
    help = 'Generates 5 articles each for the specified layout categories using Gemini API'

    def handle(self, *args, **kwargs):
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR("No GEMINI_API_KEY found in settings."))
            return

        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

        priority_order = [
            "World", "US politics", "UK", "Climate crisis", "Middle East", 
            "Ukraine", "Environment", "Science", "Global development", 
            "Football", "Tech", "Business", "Obituaries", "Iran-Israel war"
        ]

        self.stdout.write(f"Starting generation for {len(priority_order)} categories...")

        for category_name in priority_order:
            self.stdout.write(self.style.WARNING(f"\nGenerating articles for {category_name}..."))
            
            # Create or get category
            category, _ = Category.objects.get_or_create(name=category_name)

            sys_prompt = (
                f"You are an AI journalist for 'Redemption News'. Write 5 distinct, highly realistic, "
                f"and engaging news articles for the '{category_name}' section. "
                f"Each article MUST be at least 200 words long, formatted in paragraphs separated by double newlines. "
                f"Return the output strictly as a JSON array of objects, with NO markdown codeblocks. "
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
                    timeout=60
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
                    self.stdout.write(self.style.ERROR(f"Expected a JSON list, got {type(articles_data)}"))
                    continue

                for art_data in articles_data:
                    title = art_data.get('title', 'Untitled')
                    summary = art_data.get('summary', '')
                    content = art_data.get('content', '')
                    
                    if len(content) < 50:
                        continue # Skip bad generations
                        
                    NewsArticle.objects.create(
                        title=title,
                        summary=summary,
                        content=content,
                        category=category,
                    )
                    
                self.stdout.write(self.style.SUCCESS(f"Successfully generated {len(articles_data)} articles for {category_name}."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed category {category_name}: {str(e)}"))
                
            # Prevent rate limiting (Gemini API allows ~15 RPM on free tier, 3-5 seconds is usually safe)
            time.sleep(4)
            
        self.stdout.write(self.style.SUCCESS("\nAll specified categories generated successfully!"))
