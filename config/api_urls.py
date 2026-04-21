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
        'endpoints': {
            'users': {
                'register': f'{base}/api/v1/users/register/',
                'login': f'{base}/api/v1/users/login/',
                'logout': f'{base}/api/v1/users/logout/',
                'profile': f'{base}/api/v1/users/profile/',
            },
            'tests': {
                'categories': f'{base}/api/v1/tests/categories/',
                'questions': f'{base}/api/v1/tests/questions/',
                'start': f'{base}/api/v1/tests/start/',
                'history': f'{base}/api/v1/tests/history/',
            },
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('users/', include('apps.users.urls')),
    path('tests/', include('apps.tests.urls')),
]
