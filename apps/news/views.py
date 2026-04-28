from rest_framework import viewsets, permissions, filters
from rest_framework.authentication import BasicAuthentication

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
    # SessionAuthentication CSRF talab qiladi, shuning uchun o'chirildi
    authentication_classes = []
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'author']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
