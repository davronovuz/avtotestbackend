from rest_framework import viewsets, permissions, filters
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import News
from .serializers import NewsSerializer


class NewsViewSet(viewsets.ModelViewSet):
    """
    Yangiliklar uchun to'liq CRUD API.

    - GET    /api/v1/news/          — ro'yxat (barcha yangiliklar)
    - POST   /api/v1/news/          — yangi yangilik yaratish
    - GET    /api/v1/news/<id>/     — bitta yangilik
    - PUT    /api/v1/news/<id>/     — to'liq yangilash
    - PATCH  /api/v1/news/<id>/     — qisman yangilash
    - DELETE /api/v1/news/<id>/     — o'chirish
    """
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'author']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
