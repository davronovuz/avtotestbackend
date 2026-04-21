from rest_framework import serializers
from .models import Category, Question, Answer, TestSession, UserAnswer


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text']


class AnswerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'image', 'answers', 'category']


class CategorySerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'question_count']

    def get_question_count(self, obj):
        return obj.questions.count()


class TestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSession
        fields = ['id', 'category', 'total_questions', 'correct_answers', 'score',
                  'started_at', 'finished_at', 'is_finished']
        read_only_fields = ['id', 'score', 'started_at', 'finished_at']


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer_id = serializers.IntegerField()


class TestResultSerializer(serializers.ModelSerializer):
    user_answers = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = ['id', 'total_questions', 'correct_answers', 'score',
                  'started_at', 'finished_at', 'user_answers']

    def get_user_answers(self, obj):
        return [
            {
                'question': ua.question.text,
                'selected': ua.selected_answer.text if ua.selected_answer else None,
                'is_correct': ua.is_correct,
            }
            for ua in obj.user_answers.select_related('question', 'selected_answer')
        ]
