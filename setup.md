# Project Setup Guide

This document outlines how to recreate the development environment for the Redemption News Aggregator.

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
Create an isolated Python environment using `venv`. Note that the project codebase is located inside the `backend` folder.

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
*(If you do not have a requirements.txt, you can install the required packages manually:)*
```bash
pip install django djangorestframework python-dotenv pillow requests
```

### 5. Run Migrations & Database
This repository comes pre-loaded with a populated SQLite database (`db_new.sqlite3`) containing over 30 verified articles and their downloaded cover images to ensure the UI renders beautifully upon first launch. 
*(If you need to reset the database, simply delete `db_new.sqlite3` and run `python manage.py makemigrations` and `python manage.py migrate`)*

### 6. Environment Variables
Create a `.env` file in the `backend/` directory:
```bash
GEMINI_API_KEY=your_gemini_key_here
NEWSAPI_KEY=your_newsapi_key_here
```
*(Note: A fallback NewsAPI key is embedded, but you must supply a Gemini key to generate new content extensions).*

### 7. Load Sample Data (Optional)
To fetch and generate 30 fresh news articles spanning different categories using the NewsAPI + Gemini pipeline:
```bash
python manage.py generate_sections
```

### 8. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.
