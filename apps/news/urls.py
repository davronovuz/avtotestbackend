from rest_framework.routers import DefaultRouter
from .views import NewsViewSet

router = DefaultRouter()
router.register('', NewsViewSet, basename='news')

urlpatterns = router.urls
