from django.contrib import admin
from .models import (
    Section, Question, Answer,
    TestSession, UserAnswer, UserSectionProgress, MistakeLog,
)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ('number', 'text', 'is_correct', 'order')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color', 'total_questions', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('number', 'short_text', 'section', 'is_active', 'created_at')
    list_filter = ('section', 'is_active')
    search_fields = ('text', 'number')
    inlines = [AnswerInline]

    def short_text(self, obj):
        return obj.text[:80]
    short_text.short_description = 'Savol'


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'mode', 'section', 'score_percent',
                    'correct_count', 'wrong_count', 'skipped_count',
                    'status', 'started_at')
    list_filter = ('mode', 'status', 'section')
    search_fields = ('user__full_name', 'user__phone')
    readonly_fields = ('started_at', 'finished_at')


@admin.register(UserSectionProgress)
class UserSectionProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'section', 'total_attempts', 'correct_attempts', 'updated_at')
    list_filter = ('section',)


@admin.register(MistakeLog)
class MistakeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'wrong_count', 'resolved', 'last_wrong_at')
    list_filter = ('resolved',)
