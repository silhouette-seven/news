# Redemption News Aggregator

A localized, personalized news aggregation platform tailored to users. Built with Django and styled with a custom Guardian/BBC-inspired responsive grid interface embodying a retro newspaper aesthetic.

## Features
- **Retro Newspaper UI**: Features an aesthetic design with custom typography, textured paper background, and dynamic Guardian-like grid masonry layout.
- **Dynamic Content Loading**: AI agents scrape/aggregate news into the platform via Django REST Framework (DRF) JSON endpoints.
- **Categorization**: News articles are filtered into specific categories like Sports, Technology, Finance, etc.
- **Personalized Recommendations (Upcoming)**: Behavior tracking will tailor content individually.

## Documentation
- See [setup.md](setup.md) for full instructions on setting up and running the project locally.

## Architecture
- **Backend**: Python 3, Django, Django REST Framework
- **Database**: SQLite3 (Development)
- **Frontend**: Django Templates, Vanilla HTML/CSS/JS (Grid layout, Flexbox, Dynamic content logic)
