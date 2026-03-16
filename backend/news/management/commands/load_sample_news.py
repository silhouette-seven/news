import json
from django.core.management.base import BaseCommand
from news.serializers import NewsArticleIngestSerializer

class Command(BaseCommand):
    help = 'Loads sample news articles into the database for testing the UI'

    def handle(self, *args, **kwargs):
        sample_data = [
            # ==================== DIPLOMACY (Hero) ====================
            {
                "title": "Trump Unveils 'Board of Peace' Charter at Davos",
                "category": "Diplomacy",
                "tags": ["Diplomacy", "Global Order", "Politics"],
                "source_url": "https://example.com/davos",
                "summary": "Who are the founding members of Trump's new global order?",
                "content": "President Trump signed the charter for the 'Board of Peace' today, joined by leaders from the UAE, Egypt, and Argentina. While some EU nations like Germany remain skeptical of its governance, the Board aims to bypass traditional UN gridlock to tackle high-stakes mediation."
            },

            # ==================== FINANCE ====================
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
            {
                "title": "Global Oil Prices Plunge After OPEC Breakdown",
                "category": "Finance",
                "tags": ["Oil", "OPEC", "Markets"],
                "source_url": "https://example.com/oil",
                "summary": "Brent crude falls below $60 as Saudi Arabia increases output unilaterally.",
                "content": "After failing to reach consensus at the latest OPEC+ summit, Saudi Arabia announced a drastic production increase. Analysts warn this could spark a price war reminiscent of 2020, with cascading effects on energy-dependent emerging economies."
            },

            # ==================== TECHNOLOGY ====================
            {
                "title": "NVIDIA Declares the 'ChatGPT Moment' for Robotics",
                "category": "Technology",
                "tags": ["AI", "Hardware", "Robotics"],
                "source_url": "https://example.com/nvidia",
                "summary": "New physical AI models bring human-like reasoning to robots.",
                "content": "Following CES 2026, the tech world is buzzing with the release of the GR00T N1.6 dedicated to humanoid robots. NVIDIA's new architecture allows robots to perform complex chores, like folding laundry or navigating construction sites, using real-time inference."
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

            # ==================== SPORTS ====================
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
            },
            {
                "title": "Djokovic Announces Retirement After Australian Open",
                "category": "Sports",
                "tags": ["Tennis", "Grand Slam", "Retirement"],
                "source_url": "https://example.com/tennis",
                "summary": "The GOAT debate ends as Djokovic hangs up his racket with 25 grand slams.",
                "content": "In an emotional press conference at Melbourne Park, Novak Djokovic confirmed that the 2026 Australian Open was his final professional tournament. He leaves the sport with a record 25 Grand Slam titles."
            },

            # ==================== POLITICS ====================
            {
                "title": "India Passes Landmark Judicial Reform Bill",
                "category": "Politics",
                "tags": ["India", "Reform", "Judiciary"],
                "source_url": "https://example.com/india-reform",
                "summary": "Parliament clears controversial bill to restructure Supreme Court benches.",
                "content": "After weeks of heated debate, the Indian Parliament has passed the Judicial Accountability and Reform Bill. The law will restructure how benches are formed in the Supreme Court and introduce a transparent collegium process for judge appointments."
            },
            {
                "title": "UK General Election: Labour Wins Supermajority",
                "category": "Politics",
                "tags": ["UK", "Elections", "Labour"],
                "source_url": "https://example.com/uk-election",
                "summary": "Sir Keir Starmer's party secures over 420 seats in historic landslide.",
                "content": "In one of the most decisive election results in modern British history, the Labour Party has swept to power with a supermajority. The Conservatives lost over 200 seats, marking the party's worst performance since its founding."
            },
            {
                "title": "US Senate Confirms New Supreme Court Justice",
                "category": "Politics",
                "tags": ["USA", "Supreme Court", "Senate"],
                "source_url": "https://example.com/scotus",
                "summary": "Justice Elena Reyes becomes youngest appointee in over a century.",
                "content": "The US Senate narrowly confirmed Judge Elena Reyes in a 51-49 vote. At 38 years old, she is the youngest justice to join the bench in more than a century, sparking fierce debate about the politicization of the court."
            },

            # ==================== ENTERTAINMENT ====================
            {
                "title": "A24 Dominates Oscars with 'Meridian' Sweep",
                "category": "Entertainment",
                "tags": ["Oscars", "Film", "Awards"],
                "source_url": "https://example.com/oscars",
                "summary": "Studio wins Best Picture, Director, and both acting categories.",
                "content": "A24's sci-fi drama 'Meridian' took home seven Academy Awards, including Best Picture and Best Director. Critics hailed the indie powerhouse as the definitive force in modern cinema."
            },
            {
                "title": "Taylor Swift Announces Final World Tour",
                "category": "Entertainment",
                "tags": ["Music", "Tour", "Pop Culture"],
                "source_url": "https://example.com/swift",
                "summary": "The 'Eternity Tour' will span 120 shows across six continents.",
                "content": "Taylor Swift has announced that her upcoming 'Eternity Tour' will be her last global outing. Tickets are expected to generate over $2 billion in revenue, surpassing the records set by her Eras Tour."
            },
            {
                "title": "GTA VI Launch Breaks Every Gaming Record",
                "category": "Entertainment",
                "tags": ["Gaming", "Rockstar", "Launch"],
                "source_url": "https://example.com/gta6",
                "summary": "Rockstar's magnum opus sells 60 million copies in its first week.",
                "content": "Grand Theft Auto VI has shattered every entertainment launch record. The game generated $3.2 billion in its opening week, making it the most successful entertainment product launch in history, surpassing any film or album."
            },

            # ==================== SCIENCE & HEALTH ====================
            {
                "title": "First Universal Cancer Vaccine Enters Phase III Trials",
                "category": "Science & Health",
                "tags": ["Medicine", "Cancer", "Vaccine"],
                "source_url": "https://example.com/cancer-vaccine",
                "summary": "BioNTech's mRNA-based platform shows 90% efficacy across tumor types.",
                "content": "Building on the mRNA breakthroughs of the COVID-19 era, BioNTech has entered Phase III clinical trials for a universal cancer vaccine. Early results show the vaccine teaches the immune system to identify and destroy cancerous cells across multiple organ types."
            },
            {
                "title": "NASA Confirms Water Ice on Mars Surface",
                "category": "Science & Health",
                "tags": ["Space", "Mars", "NASA"],
                "source_url": "https://example.com/mars",
                "summary": "Perseverance rover drills into subsurface ice deposits near Jezero Crater.",
                "content": "In a historic confirmation, NASA has announced that the Perseverance rover has drilled into and confirmed the presence of subsurface water ice deposits near Jezero Crater. This discovery dramatically changes the viability calculus for future human missions."
            },
            {
                "title": "WHO Declares End of Global Mpox Emergency",
                "category": "Science & Health",
                "tags": ["WHO", "Public Health", "Mpox"],
                "source_url": "https://example.com/mpox",
                "summary": "Cases drop below threshold after successful global vaccination campaign.",
                "content": "The World Health Organization has officially declared the end of the Mpox public health emergency of international concern. The successful deployment of ring vaccination strategies in Central Africa was credited as the key turning point."
            },

            # ==================== ENVIRONMENT ====================
            {
                "title": "Amazon Deforestation Falls to 20-Year Low",
                "category": "Environment",
                "tags": ["Amazon", "Deforestation", "Climate"],
                "source_url": "https://example.com/amazon",
                "summary": "Satellite data confirms Brazil's aggressive conservation policies are working.",
                "content": "New data from INPE's satellite monitoring system shows deforestation in the Brazilian Amazon has fallen to its lowest level in two decades. President Lula's administration credited the success to a combination of stricter enforcement and indigenous land rights protections."
            },
            {
                "title": "Pacific Island Nation of Tuvalu Declares Climate Exile",
                "category": "Environment",
                "tags": ["Climate Change", "Tuvalu", "Migration"],
                "source_url": "https://example.com/tuvalu",
                "summary": "First sovereign nation to formally relocate its entire population due to rising seas.",
                "content": "Tuvalu has become the first country in history to begin the formal, government-organized relocation of its entire population. With the highest point in the country now regularly submerged during king tides, the government finalized a resettlement agreement with Australia and New Zealand."
            },
            {
                "title": "Europe's Largest Offshore Wind Farm Goes Online",
                "category": "Environment",
                "tags": ["Energy", "Wind", "Europe"],
                "source_url": "https://example.com/wind",
                "summary": "The 'North Sea Titan' can power 6 million homes with 4GW capacity.",
                "content": "The North Sea Titan offshore wind farm has been officially commissioned off the coast of Denmark. At 4 gigawatts, it is the largest of its kind and represents a massive step toward Europe's 2035 net-zero energy targets."
            },

            # ==================== TRENDING: ISRAEL-IRAN WAR ====================
            {
                "title": "Israel Launches Airstrikes Deep Inside Iranian Territory",
                "category": "Israel-Iran War",
                "tags": ["Israel", "Iran", "Military", "Breaking"],
                "source_url": "https://example.com/israel-iran-1",
                "summary": "Multiple military sites in Isfahan and Shiraz hit in overnight operation.",
                "content": "The Israeli Air Force conducted unprecedented strikes deep within Iranian borders, targeting nuclear research facilities and missile production sites. The operation, codenamed 'Iron Dawn', marks the most significant escalation in the decades-long shadow war between the two nations."
            },
            {
                "title": "Iran Retaliates with Missile Barrage on Israeli Military Bases",
                "category": "Israel-Iran War",
                "tags": ["Iran", "Israel", "Missiles", "Breaking"],
                "source_url": "https://example.com/israel-iran-2",
                "summary": "Iron Dome intercepts majority of incoming projectiles; casualties reported.",
                "content": "Hours after the Israeli strikes, Iran launched over 300 ballistic missiles toward Israeli territory. While the Iron Dome and Arrow defense systems intercepted the vast majority, several missiles struck the Nevatim Air Base in the Negev, causing significant damage and multiple casualties."
            },
            {
                "title": "UN Security Council Calls Emergency Session on Conflict",
                "category": "Israel-Iran War",
                "tags": ["UN", "Diplomacy", "Ceasefire"],
                "source_url": "https://example.com/israel-iran-3",
                "summary": "China and Russia block US-proposed resolution; global protests erupt.",
                "content": "The United Nations Security Council met in an emergency session to address the rapidly escalating Israel-Iran conflict. However, a US-drafted resolution calling for an immediate ceasefire was vetoed by both China and Russia, who accused Washington of a double standard in regional diplomacy."
            },
            {
                "title": "Strait of Hormuz Shipping Halts as Tensions Peak",
                "category": "Israel-Iran War",
                "tags": ["Oil", "Shipping", "Economy"],
                "source_url": "https://example.com/israel-iran-4",
                "summary": "Global oil prices spike 40% as major shipping lanes are suspended.",
                "content": "Iran has deployed naval vessels to blockade the Strait of Hormuz, through which 20% of the world's oil supply flows. Major shipping companies have suspended operations, causing crude prices to spike 40% overnight and sending shockwaves through global financial markets."
            },

            # ==================== LOCAL NEWS ====================
            {
                "title": "Salem's New Metro Line Inauguration Delayed to 2027",
                "category": "Local News",
                "tags": ["Salem", "Infrastructure", "Metro"],
                "source_url": "https://example.com/salem-metro",
                "summary": "Land acquisition disputes push timeline back by 18 months.",
                "content": "The much-anticipated Salem Metro Rail project has been pushed back to 2027 after multiple land acquisition disputes remain unresolved. Commuters who were promised relief from the city's growing traffic woes will have to wait longer."
            },
            {
                "title": "Water Rationing Announced for Southern Districts",
                "category": "Local News",
                "tags": ["Water", "TamilNadu", "Crisis"],
                "source_url": "https://example.com/water",
                "summary": "Mettur Dam levels reach critical low; agriculture sector on alert.",
                "content": "The Tamil Nadu government has announced water rationing for several southern districts after Mettur Dam water levels dropped to their lowest in a decade. Farmers have been advised to switch to less water-intensive crops for the coming season."
            },
            {
                "title": "Chennai IT Corridor Sees Record Office Space Demand",
                "category": "Local News",
                "tags": ["Chennai", "IT", "Real Estate"],
                "source_url": "https://example.com/chennai-it",
                "summary": "International tech firms drive 40% year-on-year growth in leasing.",
                "content": "Chennai's IT corridor along the Old Mahabalipuram Road has witnessed a record surge in office space leasing. The influx of international tech giants setting up their Asia-Pacific operations has transformed the corridor into one of India's most competitive business districts."
            },

            # ==================== OPINION / EDITORIAL ====================
            {
                "title": "Opinion: The Age of AI Accountability Has Arrived",
                "category": "Opinion",
                "tags": ["AI", "Ethics", "Editorial"],
                "source_url": "https://example.com/ai-opinion",
                "summary": "Why we need binding international treaties on artificial intelligence.",
                "content": "As AI systems increasingly make life-and-death decisions in healthcare, criminal justice, and finance, the absence of binding international regulation is not just a policy gap — it is a moral failure. This editorial argues for a Geneva Convention-style framework for artificial intelligence."
            },
            {
                "title": "Opinion: Cricket Has Become a Billionaires' Playground",
                "category": "Opinion",
                "tags": ["Cricket", "IPL", "Editorial"],
                "source_url": "https://example.com/cricket-opinion",
                "summary": "The soul of the game is being lost to franchise capitalism.",
                "content": "With the IPL now valued at over $15 billion, the gap between franchise cricket and international test matches has never been wider. This editorial examines how the relentless commercialization threatens the traditions and competitive integrity that made the sport great."
            },
            {
                "title": "Opinion: Remote Work is Not the Future — Hybrid Is",
                "category": "Opinion",
                "tags": ["Work", "Remote", "Corporate"],
                "source_url": "https://example.com/remote-work",
                "summary": "Why the return-to-office backlash misses the point entirely.",
                "content": "The debate between remote and office work has devolved into tribal warfare. Neither side is completely right. The real future lies in intentional hybrid models that optimize for deep work, team collaboration, and employee autonomy without sacrificing organizational culture."
            },
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
