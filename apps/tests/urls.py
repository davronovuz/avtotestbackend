from django.urls import path
from .views import (
    CategoryListView, QuestionListView,
    StartTestView, SubmitAnswerView, FinishTestView, TestHistoryView,
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('questions/', QuestionListView.as_view(), name='questions'),
    path('start/', StartTestView.as_view(), name='start-test'),
    path('sessions/<int:session_id>/answer/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('sessions/<int:session_id>/finish/', FinishTestView.as_view(), name='finish-test'),
    path('history/', TestHistoryView.as_view(), name='test-history'),
]
