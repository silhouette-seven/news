from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Custom user model, allows easy extensibility later
    pass

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    location = models.CharField(max_length=255, blank=True, null=True)
    preferred_tags = models.ManyToManyField('news.Tag', blank=True, related_name='preferring_users')

    def __str__(self):
        return f"{self.user.username}'s Profile"

class UserInteraction(models.Model):
    INTERACTION_CHOICES = [
        ('READ', 'Read'),
        ('LIKED', 'Liked'),
        ('SAVED', 'Saved'),
        ('DISLIKED', 'Disliked')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    article = models.ForeignKey('news.NewsArticle', on_delete=models.CASCADE, related_name='user_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.article.title}"
