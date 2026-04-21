from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from .models import Category, Question, TestSession, UserAnswer, Answer
from .serializers import (
    CategorySerializer, QuestionSerializer, TestSessionSerializer,
    SubmitAnswerSerializer, TestResultSerializer,
)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary='Barcha kategoriyalar')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Question.objects.prefetch_related('answers')
        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    @swagger_auto_schema(operation_summary='Savollar ro\'yxati (category=id filter)')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StartTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=TestSessionSerializer,
        responses={201: TestSessionSerializer},
        operation_summary='Yangi test boshlash',
    )
    def post(self, request):
        category_id = request.data.get('category')
        questions_qs = Question.objects.all()
        if category_id:
            questions_qs = questions_qs.filter(category_id=category_id)

        session = TestSession.objects.create(
            user=request.user,
            category_id=category_id,
            total_questions=questions_qs.count(),
        )
        return Response(TestSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class SubmitAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=SubmitAnswerSerializer,
        responses={200: 'Javob qabul qilindi'},
        operation_summary='Javob yuborish',
    )
    def post(self, request, session_id):
        try:
            session = TestSession.objects.get(id=session_id, user=request.user, is_finished=False)
        except TestSession.DoesNotExist:
            return Response({'detail': 'Sessiya topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_id = serializer.validated_data['question_id']
        answer_id = serializer.validated_data['answer_id']

        try:
            answer = Answer.objects.get(id=answer_id, question_id=question_id)
        except Answer.DoesNotExist:
            return Response({'detail': 'Javob topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        ua, created = UserAnswer.objects.get_or_create(
            session=session,
            question_id=question_id,
            defaults={'selected_answer': answer, 'is_correct': answer.is_correct},
        )
        if not created:
            ua.selected_answer = answer
            ua.is_correct = answer.is_correct
            ua.save()

        return Response({'is_correct': answer.is_correct})


class FinishTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={200: TestResultSerializer},
        operation_summary='Testni yakunlash',
    )
    def post(self, request, session_id):
        try:
            session = TestSession.objects.get(id=session_id, user=request.user, is_finished=False)
        except TestSession.DoesNotExist:
            return Response({'detail': 'Sessiya topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        correct = session.user_answers.filter(is_correct=True).count()
        total = session.total_questions
        session.correct_answers = correct
        session.score = round((correct / total * 100), 2) if total > 0 else 0
        session.is_finished = True
        session.finished_at = timezone.now()
        session.save()

        return Response(TestResultSerializer(session).data)


class TestHistoryView(generics.ListAPIView):
    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TestSession.objects.filter(user=self.request.user, is_finished=True)

    @swagger_auto_schema(operation_summary='Test tarixi')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
