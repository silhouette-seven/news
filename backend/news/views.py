from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import NewsArticle, Category, Tag
from .serializers import NewsArticleSerializer, CategorySerializer, TagSerializer, NewsArticleIngestSerializer

class NewsArticleViewSet(viewsets.ModelViewSet):
    queryset = NewsArticle.objects.all().prefetch_related('tags').select_related('category')
    
    def get_serializer_class(self):
        if self.action in ['create', 'ingest']:
            return NewsArticleIngestSerializer
        return NewsArticleSerializer

    def get_permissions(self):
        # Ideally, we would use APIKey permissions here for the AI ingest.
        # For development, we'll allow Any for reading, and later secure it.
        return [permissions.AllowAny()]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def ingest(self, request):
        """
        Endpoint for AI Agents to easily upload generated news articles.
        Accepts: title, summary, content, source_url, tags (List of strings), category (string)
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
