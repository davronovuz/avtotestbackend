from django.urls import path
from .views import (
    HomeDashboardView,
    SectionListView, SectionQuestionsView,
    StartTestView, SubmitAnswerView, FinishTestView, TestHistoryView,
    MistakeListView,
)

urlpatterns = [
    # Home ekran
    path('home/', HomeDashboardView.as_view(), name='home-dashboard'),

    # Mavzular ekrani
    path('sections/', SectionListView.as_view(), name='sections'),
    path('sections/<int:section_id>/questions/', SectionQuestionsView.as_view(), name='section-questions'),

    # Test oqimi
    path('start/', StartTestView.as_view(), name='start-test'),
    path('sessions/<int:session_id>/answer/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('sessions/<int:session_id>/finish/', FinishTestView.as_view(), name='finish-test'),
    path('history/', TestHistoryView.as_view(), name='test-history'),

    # Xatolar
    path('mistakes/', MistakeListView.as_view(), name='mistakes'),
]
