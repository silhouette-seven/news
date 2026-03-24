import time
from django.core.management.base import BaseCommand
from news.models import NewsArticle
from news.utils import generate_cover_image


class Command(BaseCommand):
    help = 'Backfill cover images for articles using Imagen 4 AI generation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-generate images even for articles that already have a cover_image',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually generating',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit the number of articles to process (0 = all)',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        limit = options['limit']

        articles = NewsArticle.objects.all()
        if not force:
            articles = articles.filter(cover_image='')

        if limit > 0:
            articles = articles[:limit]

        total = articles.count()
        self.stdout.write(f"Found {total} articles to process.")

        success = 0
        failed = 0

        for article in articles:
            self.stdout.write(f"  [{article.id}] {article.title[:60]}...")

            if dry_run:
                self.stdout.write(self.style.WARNING("       [DRY-RUN] Would generate cover image"))
                success += 1
                continue

            try:
                generate_cover_image(article)
                if article.cover_image:
                    self.stdout.write(self.style.SUCCESS(
                        f"       [OK] Saved as {article.cover_image.name}"
                    ))
                    success += 1
                else:
                    self.stdout.write(self.style.WARNING("       [SKIP] No image generated"))
                    failed += 1

                # Respect API rate limits
                time.sleep(3)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"       [FAIL] {str(e)}"))
                failed += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! {success} images {'would be ' if dry_run else ''}generated, {failed} failed."
        ))
