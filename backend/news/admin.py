from django.contrib import admin
from .models import NewsArticle, Category, Tag, BreakingNews, PersonalizedArticle


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published_date')
    list_filter = ('category', 'published_date')
    search_fields = ('title', 'summary', 'content')
    filter_horizontal = ('tags',)
    readonly_fields = ('published_date',)


@admin.register(BreakingNews)
class BreakingNewsAdmin(admin.ModelAdmin):
    list_display = ('text', 'article', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text',)
    readonly_fields = ('created_at',)


@admin.register(PersonalizedArticle)
class PersonalizedArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'topic', 'created_at', 'is_archived')
    list_filter = ('topic', 'is_archived', 'created_at')
    search_fields = ('title', 'summary', 'content')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'generated_date')
