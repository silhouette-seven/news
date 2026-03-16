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

### 5. Run Migrations
Generate the required local database structure for the Users and News apps.
```bash
python manage.py makemigrations users news
python manage.py migrate
```

### 6. Load Sample Data (Optional)
To test the retro grid UI layout, you can generate 10 sample news articles spanning different categories using the built-in management script:
```bash
python manage.py load_sample_news
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.
