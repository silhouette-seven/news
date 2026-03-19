# Redemption News Local Development Setup

## Prerequisites
- Python 3.10+
- Git

## Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news/backend
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables Config**
   Create a `.env` file in the `backend` directory (alongside `manage.py`) and add your Gemini API Key. It is required for the AI functionality.
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run Database Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create an Admin Superuser (Optional)**
   This allows you to access the Django admin panel and manage content.
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```
   The application will be accessible at `http://127.0.0.1:8000/`.
