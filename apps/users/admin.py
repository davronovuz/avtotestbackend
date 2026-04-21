from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone', 'full_name')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('phone', 'full_name', 'avatar', 'is_active', 'is_staff')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ('phone', 'full_name', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('phone', 'full_name')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ("Shaxsiy ma'lumotlar", {'fields': ('full_name', 'avatar')}),
        ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'full_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
