from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, validate_phone


class RegisterSerializer(serializers.ModelSerializer):
    """
    Register ekrani uchun:
    - Ism va Familiya (full_name)
    - Telefon raqam (+998...)
    - Parol
    """
    password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['full_name', 'phone', 'password']
        extra_kwargs = {
            'phone': {'validators': [validate_phone]},
        }

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Login ekrani uchun:
    - Telefon raqam
    - Parol
    """
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(phone=data['phone'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Telefon raqam yoki parol noto'g'ri.")
        if not user.is_active:
            raise serializers.ValidationError("Hisob faol emas.")
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """Profil va home ekrandagi 'Salom, <ism>!' uchun."""
    first_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'phone', 'full_name', 'first_name', 'avatar', 'created_at']
        read_only_fields = ['id', 'created_at']


class TokenSerializer(serializers.Serializer):
    """JWT token javobi uchun."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

    @classmethod
    def for_user(cls, user):
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }
