import json
from django.core.management.base import BaseCommand
from news.serializers import NewsArticleIngestSerializer

class Command(BaseCommand):
    help = 'Loads sample news articles into the database for testing the UI'

    def handle(self, *args, **kwargs):
        sample_data = [
            # Hero / Diplomacy
            {
                "title": "Trump Unveils 'Board of Peace' Charter at Davos",
                "category": "Diplomacy",
                "tags": ["Diplomacy", "Global Order", "Politics"],
                "source_url": "https://example.com/davos",
                "summary": "Who are the founding members of Trump’s new global order?",
                "content": "President Trump signed the charter for the 'Board of Peace' today, joined by leaders from the UAE, Egypt, and Argentina. While some EU nations like Germany remain skeptical of its governance, the Board aims to bypass traditional UN gridlock to tackle high-stakes mediation."
            },
            
            # Finance
            {
                "title": "Indian Rupee Hits Record Low Amid Volatility",
                "category": "Finance",
                "tags": ["Economy", "Currency", "Markets"],
                "source_url": "https://example.com/rupee",
                "summary": "Currency falls to 91.96 against USD as foreign outflows intensify.",
                "content": "The Indian currency posted its steepest weekly decline in six months. Market analysts point to heightened concerns surrounding new US trade tariffs and geopolitical tensions in the Arctic as the primary drivers for the sustained selling by foreign institutional investors."
            },
            {
                "title": "Bitcoin Crosses $110,000 Support Level",
                "category": "Finance",
                "tags": ["Crypto", "Markets", "Economy"],
                "source_url": "https://example.com/crypto",
                "summary": "Institutional investors continue massive accumulation.",
                "content": "Following the latest favorable regulatory shifts in major Asian markets, Bitcoin has firmly crossed the $110,000 threshold. Traditional banking institutions are now rushing to offer ETF equivalents to their corporate clients."
            },
            {
                "title": "Federal Reserve Signals Final Rate Cut",
                "category": "Finance",
                "tags": ["Banking", "Economy", "Fed"],
                "source_url": "https://example.com/fed",
                "summary": "Powell indicates inflation targets have been sustainably met.",
                "content": "The Federal Reserve wrapped up its Q1 meetings today. Chairman Powell gave his strongest signal yet that the aggressive rate-cutting cycle of 2025 is complete, aiming for a stable baseline interest environment."
            },

            # Technology
            {
                "title": "NVIDIA Declares the 'ChatGPT Moment' for Robotics",
                "category": "Technology",
                "tags": ["AI", "Hardware", "Robotics"],
                "source_url": "https://example.com/nvidia",
                "summary": "New physical AI models bring human-like reasoning to robots.",
                "content": "Following CES 2026, the tech world is buzzing with the release of the GR00T N1.6 dedicated to humanoid robots. NVIDIA’s new architecture allows robots to perform complex chores, like folding laundry or navigating construction sites, using real-time inference."
            },
            {
                "title": "Quantum Supremacy Achieved by European Consortium",
                "category": "Technology",
                "tags": ["Quantum", "Computing", "Europe"],
                "source_url": "https://example.com/quantum",
                "summary": "New 1000-qubit processor solves 10-year problem in seconds.",
                "content": "The OQS consortium has officially published undeniable proof of quantum supremacy on a practical, fault-tolerant scale, causing massive ripples throughout the global cryptography community."
            },
            {
                "title": "Solid-State EV Batteries Hit Mass Production",
                "category": "Technology",
                "tags": ["EV", "Green Tech", "Automotive"],
                "source_url": "https://example.com/ev",
                "summary": "Toyota and Panasonic joint venture ships first million units.",
                "content": "The promised era of 800-mile electric vehicle ranges has arrived, as the joint venture finally solves the scaling issues associated with solid-state electrolytes. The first models hit dealerships next month."
            },

            # Sports
            {
                "title": "T20 World Cup Turmoil: Bangladesh Withdraws",
                "category": "Sports",
                "tags": ["Cricket", "T20", "Asia"],
                "source_url": "https://example.com/cricket",
                "summary": "Scotland expected to replace Bangladesh after BCB refuses to play.",
                "content": "The ICC has rejected Bangladesh's request to move their matches to a neutral venue. As the tournament approaches, the BCB has officially pulled out, sparking a massive debate about sports diplomacy and the upcoming February tournament co-hosted by India and Sri Lanka."
            },
            {
                "title": "Real Madrid Completes Historic Treble",
                "category": "Sports",
                "tags": ["Football", "Soccer", "La Liga"],
                "source_url": "https://example.com/soccer",
                "summary": "Vinicius Jr. scores winning goal in 89th minute of CL Final.",
                "content": "Madrid's dominance over European football continues as they staged an incredible late comeback to steal the Champions League trophy, securing their domestic and international treble."
            },
            {
                "title": "NBA Expands to Seattle and Las Vegas",
                "category": "Sports",
                "tags": ["Basketball", "NBA", "Expansion"],
                "source_url": "https://example.com/nba",
                "summary": "Commission approves 32-team format starting 2027 season.",
                "content": "The long-awaited return of the SuperSonics is officially locked in. The NBA board of governors unanimously voted to expand the league, pushing the competitive landscape into a new era with massive broadcasting implications."
            }
        ]

        count = 0
        for data in sample_data:
            serializer = NewsArticleIngestSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                count += 1
            else:
                self.stderr.write(f"Failed to load: {data['title']} - {serializer.errors}")

        self.stdout.write(self.style.SUCCESS(f'Successfully ingested {count} sample articles.'))
