import time
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from news.models import NewsArticle
from news.utils import get_relevant_image


class Command(BaseCommand):
    help = 'Backfill cover images for all articles using Wikipedia title-based image search'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-download images even for articles that already have a cover_image',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually downloading',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        articles = NewsArticle.objects.all()
        if not force:
            articles = articles.filter(cover_image='')

        total = articles.count()
        self.stdout.write(f"Found {total} articles to process.")

        success = 0
        failed = 0

        for article in articles:
            self.stdout.write(f"  [{article.id}] {article.title[:60]}...")

            try:
                image_url = get_relevant_image(article.title)
                self.stdout.write("       -> Image URL: {}...".format(image_url[:80]))

                if dry_run:
                    success += 1
                    continue

                # Download the image
                resp = requests.get(image_url, timeout=15, headers={
                    'User-Agent': 'AntigravityNewsBot/1.0'
                })
                resp.raise_for_status()

                # Determine extension from content type
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
                if 'png' in content_type:
                    ext = 'png'
                elif 'gif' in content_type:
                    ext = 'gif'
                elif 'webp' in content_type:
                    ext = 'webp'
                elif 'svg' in content_type:
                    # Skip SVGs, they won't work well as cover images
                    self.stdout.write(self.style.WARNING("       [SKIP] Skipped SVG image"))
                    failed += 1
                    continue
                else:
                    ext = 'jpg'

                # Save to the cover_image field
                filename = f"article_{article.id}_cover.{ext}"
                article.cover_image.save(
                    filename,
                    ContentFile(resp.content),
                    save=True
                )
                self.stdout.write(self.style.SUCCESS("       [OK] Saved as {}".format(filename)))
                success += 1

                # Be polite to Wikipedia API
                time.sleep(2)

            except Exception as e:
                self.stdout.write(self.style.ERROR("       [FAIL] Failed: {}".format(str(e))))
                failed += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! {success} images {'would be ' if dry_run else ''}downloaded, {failed} failed."
        ))
