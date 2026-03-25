import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import NewsArticle, Category, Tag
from news.newsapi import fetch_and_extend_news

BATCH_SIZE = 5
TOTAL_TARGET = 20

print(f"Generating up to {TOTAL_TARGET} articles using newsapi pipeline...")

generated_count = 0
batches = (TOTAL_TARGET + BATCH_SIZE - 1) // BATCH_SIZE

for batch_num in range(batches):
    remaining = TOTAL_TARGET - generated_count
    if remaining <= 0:
        break

    count = min(BATCH_SIZE, remaining)
    print(f"\n[Batch {batch_num + 1}/{batches}] Fetching {count} articles...")

    try:
        articles_data = fetch_and_extend_news(count=count)
        if not articles_data:
            print("  -> No articles returned, skipping batch.")
            continue

        for ad in articles_data:
            # Use the pipeline-detected category
            category_name = ad.get('category', 'World')
            cat, _ = Category.objects.get_or_create(name=category_name)

            article = NewsArticle.objects.create(
                title=ad.get('title', 'Untitled')[:255],
                summary=ad.get('summary', ''),
                content=ad.get('content', ''),
                category=cat,
                source_url=ad.get('source_url', ''),
                cover_image_url=ad.get('cover_image_url', ''),
            )

            tags_list = ad.get('tags', [])
            for t_name in tags_list[:3]:
                t_name = str(t_name).strip()[:50]
                if t_name:
                    tag_obj, _ = Tag.objects.get_or_create(name=t_name)
                    article.tags.add(tag_obj)

            print(f"  -> Saved article ID {article.id} in category '{category_name}'")
            generated_count += 1

    except Exception as e:
        print(f"  -> Batch error: {e}")

    # Respect rate limits between batches
    if batch_num < batches - 1:
        print("  -> Sleeping 15 seconds to respect API rate limits...")
        time.sleep(15)

print(f"\nDone generating {generated_count} articles.")
