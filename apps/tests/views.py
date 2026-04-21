import random
from django.db.models import Avg, Count
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from .models import (
    Section, Question, Answer,
    TestSession, UserAnswer, UserSectionProgress, MistakeLog,
)
from .serializers import (
    SectionListSerializer, QuestionSerializer, QuestionWithAnswersSerializer,
    StartTestSerializer, TestSessionSerializer, SubmitAnswerSerializer,
    TestResultSerializer, HomeDashboardSerializer, MistakeSerializer,
)


# ==================== HOME ====================

class HomeDashboardView(APIView):
    """
    Home ekran uchun birlashtirilgan ma'lumot.
    GET /api/v1/tests/home/
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={200: HomeDashboardSerializer},
        operation_summary="Home ekran (greeting, overall %, mistakes, etc.)",
    )
    def get(self, request):
        user = request.user
        sessions = TestSession.objects.filter(user=user, status=TestSession.Status.FINISHED)
        total_sessions = sessions.count()
        overall = sessions.aggregate(avg=Avg('score_percent'))['avg'] or 0
        last = sessions.first()
        mistakes_count = MistakeLog.objects.filter(user=user, resolved=False).count()

        if overall >= 90:
            msg = "Ajoyib! Siz imtihonga tayyorsiz."
        elif overall >= 70:
            msg = "Siz imtihonga deyarli tayyorsiz!"
        elif overall >= 40:
            msg = "Yaxshi boshlanish, yana mashq qiling."
        else:
            msg = "Boshlaymizmi? Har kuni mashq qiling."

        data = {
            'greeting': f"Salom, {user.first_name}!",
            'overall_percent': round(overall, 1),
            'total_sessions': TestSession.objects.filter(user=user).count(),
            'finished_sessions': total_sessions,
            'mistakes_count': mistakes_count,
            'last_session_score': last.score_percent if last else None,
            'motivational_message': msg,
        }
        return Response(HomeDashboardSerializer(data).data)


# ==================== SECTIONS ====================

class SectionListView(generics.ListAPIView):
    """
    GET /api/v1/tests/sections/
    Mavzular ekrani: Yo'l belgilari, Qoidalar, Jarimalar.
    """
    queryset = Section.objects.filter(is_active=True)
    serializer_class = SectionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Bo'limlar ro'yxati (progress % bilan)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SectionQuestionsView(generics.ListAPIView):
    """
    GET /api/v1/tests/sections/<id>/questions/
    Bir bo'limning barcha savollari (o'rganish uchun).
    """
    serializer_class = QuestionWithAnswersSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(
            section_id=self.kwargs['section_id'], is_active=True,
        ).prefetch_related('answers')

    @swagger_auto_schema(operation_summary="Bo'lim savollari (to'g'ri javoblari bilan)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==================== TEST FLOW ====================

class StartTestView(APIView):
    """
    POST /api/v1/tests/start/
    Yangi test sessiyasini boshlash.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=StartTestSerializer,
        responses={201: TestSessionSerializer},
        operation_summary="Test boshlash (random/section/mistakes)",
    )
    def post(self, request):
        serializer = StartTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mode = serializer.validated_data['mode']
        section_id = serializer.validated_data.get('section_id')
        limit = serializer.validated_data['limit']

        qs = Question.objects.filter(is_active=True)
        section = None

        if mode == TestSession.Mode.BY_SECTION:
            if not section_id:
                return Response({'detail': 'section_id majburiy.'}, status=status.HTTP_400_BAD_REQUEST)
            section = Section.objects.filter(id=section_id).first()
            if not section:
                return Response({'detail': "Bo'lim topilmadi."}, status=status.HTTP_404_NOT_FOUND)
            qs = qs.filter(section=section)

        elif mode == TestSession.Mode.MISTAKES:
            wrong_ids = MistakeLog.objects.filter(
                user=request.user, resolved=False,
            ).values_list('question_id', flat=True)
            qs = qs.filter(id__in=list(wrong_ids))
            if not qs.exists():
                return Response(
                    {'detail': "Xatolaringiz yo'q, ajoyib!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        ids = list(qs.values_list('id', flat=True))
        random.shuffle(ids)
        selected = ids[:limit]

        session = TestSession.objects.create(
            user=request.user,
            mode=mode,
            section=section,
            question_ids=selected,
            total_questions=len(selected),
            time_limit_seconds=len(selected) * 60,
        )
        return Response(
            TestSessionSerializer(session, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class SubmitAnswerView(APIView):
    """
    POST /api/v1/tests/sessions/<id>/answer/
    Test paytida bitta savolga javob yuborish (yoki skip).
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=SubmitAnswerSerializer,
        operation_summary="Javob yuborish (skipped=true o'tkazib yuborish)",
    )
    def post(self, request, session_id):
        session = TestSession.objects.filter(
            id=session_id, user=request.user, status=TestSession.Status.ONGOING,
        ).first()
        if not session:
            return Response({'detail': 'Sessiya topilmadi yoki tugagan.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        q_id = serializer.validated_data['question_id']
        a_id = serializer.validated_data.get('answer_id')
        skipped = serializer.validated_data['skipped']

        if q_id not in session.question_ids:
            return Response({'detail': "Savol bu sessiyaga tegishli emas."}, status=400)

        answer = None
        is_correct = False
        if not skipped:
            answer = Answer.objects.filter(id=a_id, question_id=q_id).first()
            if not answer:
                return Response({'detail': 'Variant topilmadi.'}, status=status.HTTP_404_NOT_FOUND)
            is_correct = answer.is_correct

        ua, _ = UserAnswer.objects.update_or_create(
            session=session, question_id=q_id,
            defaults={'selected_answer': answer, 'is_correct': is_correct, 'is_skipped': skipped},
        )

        # Section progress yangilash
        question = Question.objects.get(id=q_id)
        progress, _ = UserSectionProgress.objects.get_or_create(
            user=request.user, section=question.section,
        )
        progress.total_attempts += 1
        if is_correct:
            progress.correct_attempts += 1
            if q_id not in progress.mastered_question_ids:
                progress.mastered_question_ids.append(q_id)
        progress.save()

        # Mistake log
        if skipped or not is_correct:
            mistake, created = MistakeLog.objects.get_or_create(
                user=request.user, question_id=q_id,
                defaults={'resolved': False},
            )
            if not created:
                mistake.wrong_count += 1
                mistake.resolved = False
                mistake.save()
        else:
            MistakeLog.objects.filter(
                user=request.user, question_id=q_id,
            ).update(resolved=True)

        return Response({
            'is_correct': is_correct,
            'is_skipped': skipped,
            'correct_answer_id': question.answers.filter(is_correct=True).values_list('id', flat=True).first(),
        })


class FinishTestView(APIView):
    """
    POST /api/v1/tests/sessions/<id>/finish/
    Testni yakunlash va natijani olish.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={200: TestResultSerializer},
        operation_summary="Testni yakunlash (18/20 natija)",
    )
    def post(self, request, session_id):
        session = TestSession.objects.filter(
            id=session_id, user=request.user, status=TestSession.Status.ONGOING,
        ).first()
        if not session:
            return Response({'detail': 'Sessiya topilmadi yoki allaqachon yakunlangan.'}, status=404)

        session.finish()
        return Response(TestResultSerializer(session).data)


class TestHistoryView(generics.ListAPIView):
    """GET /api/v1/tests/history/ — foydalanuvchining tugallangan testlari."""
    serializer_class = TestResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TestSession.objects.filter(
            user=self.request.user, status=TestSession.Status.FINISHED,
        )

    @swagger_auto_schema(operation_summary="Yakunlangan testlar tarixi")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==================== MISTAKES ====================

class MistakeListView(generics.ListAPIView):
    """
    GET /api/v1/tests/mistakes/
    "Xatolarni ko'rish" — hali tuzatilmagan xatolar ro'yxati.
    """
    serializer_class = MistakeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MistakeLog.objects.filter(user=self.request.user, resolved=False).select_related('question__section').prefetch_related('question__answers')

    @swagger_auto_schema(operation_summary="Mening xatolarim")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
