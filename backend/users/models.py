from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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


class UserTagScore(models.Model):
    """Weighted tag preferences per user — powers the personalized feed ranking."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tag_scores')
    tag = models.ForeignKey('news.Tag', on_delete=models.CASCADE, related_name='user_scores')
    score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'tag')
        ordering = ['-score']

    def __str__(self):
        return f"{self.user.username} → {self.tag.name}: {self.score:.1f}"

    INTERACTION_WEIGHTS = {
        'READ': 1.0,
        'LIKED': 3.0,
        'SAVED': 5.0,
        'DISLIKED': -2.0,
    }

    @classmethod
    def recalculate_for_user(cls, user):
        """Recalculate all tag scores for a user based on their full interaction history."""
        from news.models import Tag
        now = timezone.now()
        interactions = UserInteraction.objects.filter(user=user).select_related('article').prefetch_related('article__tags')

        tag_totals = {}
        for interaction in interactions:
            weight = cls.INTERACTION_WEIGHTS.get(interaction.interaction_type, 0)
            days_since = max((now - interaction.timestamp).total_seconds() / 86400, 0)
            recency = 1.0 / (1.0 + days_since * 0.1)
            delta = weight * recency

            for tag in interaction.article.tags.all():
                tag_totals[tag.id] = tag_totals.get(tag.id, 0) + delta

        # Update or create tag scores
        for tag_id, total_score in tag_totals.items():
            cls.objects.update_or_create(
                user=user,
                tag_id=tag_id,
                defaults={'score': max(total_score, 0)}
            )

        # Remove tags that have dropped to zero
        cls.objects.filter(user=user, score__lte=0).delete()

    @classmethod
    def bump_for_article(cls, user, article, interaction_type):
        """Quick bump: add score for an article's tags without full recalculation."""
        weight = cls.INTERACTION_WEIGHTS.get(interaction_type, 0)
        for tag in article.tags.all():
            obj, created = cls.objects.get_or_create(
                user=user,
                tag=tag,
                defaults={'score': max(weight, 0)}
            )
            if not created:
                obj.score = max(obj.score + weight, 0)
                obj.save()

    @classmethod
    def get_top_tags(cls, user, limit=10):
        """Return the user's top-N tags by score."""
        return cls.objects.filter(user=user).select_related('tag').order_by('-score')[:limit]
