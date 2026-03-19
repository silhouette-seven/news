from django.urls import path
from . import views

urlpatterns = [
    path('signin/', views.signin_view, name='signin'),
    path('signout/', views.signout_view, name='signout'),
    path('feed/', views.feed_view, name='feed'),
    path('feed/generate/', views.generate_personalized_articles, name='generate_personalized_articles'),
    path('article/ai/<int:article_id>/', views.personalized_article_detail_view, name='personalized_article'),
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),
    path('ai-assistant/search/', views.ai_search_articles, name='ai_search'),
    path('ai-assistant/ask/', views.ai_ask_gemini, name='ai_ask'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/save-interests/', views.save_interests_view, name='save_interests'),
]
