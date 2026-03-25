# Geo-News — Project Setup Guide

This document outlines how to set up the development environment for the Geo-News Aggregator.

## Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- **Git**

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository_url>
cd news
```

### 2. Create the Virtual Environment
```bash
# Windows
python -m venv backend\venv

# MacOS / Linux
python3 -m venv backend/venv
```

### 3. Activate the Environment
```bash
# Windows
backend\venv\Scripts\activate

# MacOS / Linux
source backend/venv/bin/activate
```

### 4. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```
If `requirements.txt` is missing:
```bash
pip install django djangorestframework python-dotenv pillow requests
```

### 5. Environment Variables
Create a `.env` file in the `backend/` directory (alongside `manage.py`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

| Key | Required | Purpose |
|-----|----------|---------|
| `GEMINI_API_KEY` | **Yes** | Powers AI article extension, personalized articles, and AI assistant |
| `NEWSAPI_KEY` | **Yes** | Fetches real news headlines from NewsAPI.org |
| `ELEVENLABS_API_KEY` | Optional | Enables article voiceover / TTS feature |

> **Note:** Get a free Gemini API key at https://aistudio.google.com/apikey and a free NewsAPI key at https://newsapi.org/register.

### 6. Database
This repository ships with a pre-populated SQLite database (`db_new.sqlite3`) containing articles and cover images so the UI renders on first launch.

To **use the existing database** — no action needed.

To **reset and start fresh**:
```bash
del db_new.sqlite3        # Windows
# rm db_new.sqlite3       # Mac/Linux
python manage.py makemigrations
python manage.py migrate
```

### 7. Create an Admin Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 8. Bulk Generate Articles (Optional)
To populate with 20 fresh articles from NewsAPI + Gemini:
```bash
python bulk_generate.py
```

### 9. Run the Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser.

## Key Features

| Feature | Description |
|---------|-------------|
| **Breaking News** | Country-based headlines via NewsAPI, auto-categorized |
| **Local News** | Location-based articles generated on first visit |
| **Personalized Feed** | Articles tailored to user interests and tag scores |
| **Show My Article** | Daily 200-300 word personalized briefing (1 per day) |
| **AI Assistant** | Ask AI questions about any article |
| **Article Voiceover** | TTS using ElevenLabs (requires API key) |
| **Dashboard** | Admin panel for article management at `/dashboard/` |

## Project Structure
```
news/
├── backend/
│   ├── core/           # Django settings, URLs
│   ├── news/           # News app (models, views, pipeline)
│   │   ├── newsapi.py  # Central news pipeline (NewsAPI + Gemini)
│   │   ├── breaking_news_task.py
│   │   ├── tts_views.py
│   │   └── ...
│   ├── users/          # User management, feed, interactions
│   ├── templates/      # HTML templates
│   ├── static/         # CSS, images
│   ├── bulk_generate.py
│   ├── manage.py
│   └── .env            # API keys (not committed)
└── setup.md
```
