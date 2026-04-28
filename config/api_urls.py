from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    base = request.build_absolute_uri('/')[:-1]
    return Response({
        'message': 'Avtotest API v1 — xush kelibsiz!',
        'docs': {
            'swagger': f'{base}/swagger/',
            'redoc': f'{base}/redoc/',
        },
        'auth': {
            'register': f'{base}/api/v1/users/register/',
            'login': f'{base}/api/v1/users/login/',
            'token_refresh': f'{base}/api/v1/users/token/refresh/',
            'profile': f'{base}/api/v1/users/profile/',
        },
        'home_screen': {
            'dashboard': f'{base}/api/v1/tests/home/',
        },
        'sections_screen': {
            'list': f'{base}/api/v1/tests/sections/',
            'questions': f'{base}/api/v1/tests/sections/<id>/questions/',
        },
        'test_flow': {
            'start': f'{base}/api/v1/tests/start/',
            'submit_answer': f'{base}/api/v1/tests/sessions/<id>/answer/',
            'finish': f'{base}/api/v1/tests/sessions/<id>/finish/',
            'history': f'{base}/api/v1/tests/history/',
        },
        'mistakes_screen': {
            'list': f'{base}/api/v1/tests/mistakes/',
        },
        'news': {
            'list':   f'{base}/api/v1/news/',
            'detail': f'{base}/api/v1/news/<id>/',
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('users/', include('apps.users.urls')),
    path('tests/', include('apps.tests.urls')),
    path('news/', include('apps.news.urls')),
]
