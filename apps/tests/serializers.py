from rest_framework import serializers
from .models import (
    Section, Question, Answer,
    TestSession, UserAnswer, UserSectionProgress, MistakeLog,
)


# ==================== SECTION ====================

class SectionListSerializer(serializers.ModelSerializer):
    """
    Mavzular ekrani uchun:
    icon, name, description, progress %.
    """
    progress_percent = serializers.SerializerMethodField()
    total_questions = serializers.ReadOnlyField()

    class Meta:
        model = Section
        fields = ['id', 'name', 'description', 'icon', 'color',
                  'total_questions', 'progress_percent']

    def get_progress_percent(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return 0
        progress = obj.user_progress.filter(user=user).first()
        return progress.progress_percent if progress else 0


# ==================== ANSWER / QUESTION ====================

class AnswerPublicSerializer(serializers.ModelSerializer):
    """Test ishlayotganda ko'rinadi — is_correct yashirilgan."""
    class Meta:
        model = Answer
        fields = ['id', 'number', 'text']


class AnswerDetailSerializer(serializers.ModelSerializer):
    """Javob berilgandan keyin yoki xatolar ro'yxatida — is_correct ochiq."""
    class Meta:
        model = Answer
        fields = ['id', 'number', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    """Test ekranidagi bitta savol."""
    answers = AnswerPublicSerializer(many=True, read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'number', 'text', 'description', 'image',
                  'section', 'section_name', 'answers']


class QuestionWithAnswersSerializer(serializers.ModelSerializer):
    """Xatolarni ko'rish uchun — to'g'ri javob ham ko'rinadi."""
    answers = AnswerDetailSerializer(many=True, read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'number', 'text', 'description', 'image',
                  'explanation', 'section', 'section_name', 'answers']


# ==================== TEST SESSION ====================

class StartTestSerializer(serializers.Serializer):
    """
    Yangi test boshlash so'rovi.
    mode: random | section | mistakes
    section_id: agar mode=section bo'lsa
    """
    mode = serializers.ChoiceField(choices=TestSession.Mode.choices, default=TestSession.Mode.RANDOM)
    section_id = serializers.IntegerField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)


class TestSessionSerializer(serializers.ModelSerializer):
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    questions = serializers.SerializerMethodField()
    time_spent_seconds = serializers.ReadOnlyField()

    class Meta:
        model = TestSession
        fields = ['id', 'mode', 'mode_display', 'status', 'section',
                  'total_questions', 'correct_count', 'wrong_count',
                  'skipped_count', 'score_percent',
                  'time_limit_seconds', 'time_spent_seconds',
                  'started_at', 'finished_at', 'questions']
        read_only_fields = ['status', 'correct_count', 'wrong_count',
                            'skipped_count', 'score_percent',
                            'started_at', 'finished_at']

    def get_questions(self, obj):
        if not obj.question_ids:
            return []
        questions = Question.objects.filter(id__in=obj.question_ids).prefetch_related('answers')
        ordered = {q.id: q for q in questions}
        ordered_list = [ordered[qid] for qid in obj.question_ids if qid in ordered]
        return QuestionSerializer(ordered_list, many=True, context=self.context).data


class SubmitAnswerSerializer(serializers.Serializer):
    """Test paytida bitta savolga javob yuborish."""
    question_id = serializers.IntegerField()
    answer_id = serializers.IntegerField(required=False, allow_null=True)
    skipped = serializers.BooleanField(default=False)


class TestResultSerializer(serializers.ModelSerializer):
    """
    Natija ekrani uchun: 18/20, to'g'ri/noto'g'ri, vaqt.
    """
    time_spent_seconds = serializers.ReadOnlyField()
    wrong_questions = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = ['id', 'total_questions', 'correct_count', 'wrong_count',
                  'skipped_count', 'score_percent', 'time_spent_seconds',
                  'started_at', 'finished_at', 'wrong_questions']

    def get_wrong_questions(self, obj):
        """Xato javob berilgan savollar — natija ekranidan keyin ko'rish uchun."""
        wrong = obj.user_answers.filter(is_correct=False).select_related('question', 'selected_answer')
        return [
            {
                'question_id': ua.question_id,
                'question_text': ua.question.text,
                'selected_text': ua.selected_answer.text if ua.selected_answer else None,
                'is_skipped': ua.is_skipped,
            }
            for ua in wrong
        ]


# ==================== HOME / DASHBOARD ====================

class HomeDashboardSerializer(serializers.Serializer):
    """
    Home ekran uchun to'liq ma'lumot:
    - greeting (Salom, <first_name>!)
    - overall % (sizning natijangiz)
    - mistakes_count (xatolarni ko'rish)
    - total_sessions
    """
    greeting = serializers.CharField()
    overall_percent = serializers.FloatField()
    total_sessions = serializers.IntegerField()
    finished_sessions = serializers.IntegerField()
    mistakes_count = serializers.IntegerField()
    last_session_score = serializers.FloatField(allow_null=True)
    motivational_message = serializers.CharField()


# ==================== MISTAKE LOG ====================

class MistakeSerializer(serializers.ModelSerializer):
    question = QuestionWithAnswersSerializer(read_only=True)

    class Meta:
        model = MistakeLog
        fields = ['id', 'question', 'wrong_count', 'last_wrong_at', 'resolved']
