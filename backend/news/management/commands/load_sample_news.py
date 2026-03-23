from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Previously loaded sample news articles. Now cleared — use generate_sections command to populate with real news.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(
            "This command no longer loads sample data.\n"
            "Fictional sample articles have been removed to ensure news reliability.\n"
            "Use 'python manage.py generate_sections' to populate with real, AI-sourced news articles."
        ))
