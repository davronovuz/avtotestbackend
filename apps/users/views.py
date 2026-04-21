from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, TokenSerializer,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: 'JWT token + user', 400: 'Validation error'},
        operation_summary="Ro'yxatdan o'tish (full_name + phone + password)",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(TokenSerializer.for_user(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: 'JWT token + user'},
        operation_summary='Tizimga kirish (phone + password)',
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(TokenSerializer.for_user(serializer.validated_data['user']))


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(operation_summary="Profil (full_name, phone, avatar)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
