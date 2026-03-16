from rest_framework import serializers
from .models import NewsArticle, Category, Tag

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class NewsArticleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = '__all__'

class NewsArticleIngestSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100), write_only=True, required=False
    )
    category = serializers.CharField(max_length=100, write_only=True, required=False)

    class Meta:
        model = NewsArticle
        fields = ['title', 'summary', 'content', 'source_url', 'tags', 'category']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        category_name = validated_data.pop('category', None)
        
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name)
            validated_data['category'] = category

        article = NewsArticle.objects.create(**validated_data)

        for tag_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            article.tags.add(tag)

        return article
