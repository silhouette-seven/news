from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField()
    source_url = models.URLField(max_length=500, blank=True, null=True)
    cover_image = models.ImageField(upload_to='article_covers/', blank=True, null=True)
    published_date = models.DateTimeField(auto_now_add=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')

    class Meta:
        ordering = ['-published_date']

from django.conf import settings

class PersonalizedArticle(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personalized_articles')
    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField()
    cover_image_url = models.URLField(max_length=500, blank=True, null=True)
    topic = models.CharField(max_length=100)
    tags = models.ManyToManyField('Tag', blank=True, related_name='personalized_articles')
    created_at = models.DateTimeField(auto_now_add=True)
    generated_date = models.DateField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.owner.username} - {self.title}"

class BreakingNews(models.Model):
    text = models.CharField(max_length=500)
    article = models.ForeignKey(NewsArticle, on_delete=models.SET_NULL, null=True, blank=True, related_name='breaking_news_entries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.text

class ArticleAudio(models.Model):
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='audio_versions')
    voice_id = models.CharField(max_length=50)
    audio_file = models.FileField(upload_to='tts/', max_length=500)
    alignment_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'voice_id')

    def __str__(self):
        return f"Audio for {self.article.title} (Voice: {self.voice_id})"

class DailyPodcast(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='podcasts')
    date = models.DateField(auto_now_add=True)
    audio_file = models.FileField(upload_to='podcasts/', max_length=500)
    script = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"Podcast for {self.user.username} on {self.date}"
