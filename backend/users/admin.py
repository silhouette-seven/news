from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, UserInteraction, UserTagScore


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    pass


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location')
    search_fields = ('user__username', 'location')
    filter_horizontal = ('preferred_tags',)


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'interaction_type', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__username', 'article__title')
    readonly_fields = ('timestamp',)


@admin.register(UserTagScore)
class UserTagScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'score', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user__username', 'tag__name')
    readonly_fields = ('updated_at',)
