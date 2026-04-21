from django.contrib import admin
from .models import Category, Question, Answer, TestSession, UserAnswer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'category', 'created_at']
    list_filter = ['category']
    inlines = [AnswerInline]


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'score', 'is_finished', 'started_at']
    list_filter = ['is_finished', 'category']
