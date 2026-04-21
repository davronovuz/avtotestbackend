from django.db import models
from django.utils import timezone
from apps.users.models import User


class Section(models.Model):
    """
    Mavzular ekranidagi asosiy bo'limlar.
    Masalan: "Yo'l belgilari", "Qoidalar", "Jarimalar".
    """
    name = models.CharField(max_length=100, help_text="Masalan: Yo'l belgilari")
    description = models.CharField(
        max_length=255,
        help_text="Masalan: Barcha yo'l belgilarini o'rganing",
    )
    icon = models.ImageField(
        upload_to='sections/icons/',
        null=True, blank=True,
        help_text="Bo'lim ikonkasi (Yo'l belgilari uchun qizil svetofor va h.k.)",
    )
    color = models.CharField(
        max_length=7,
        default='#4F80FF',
        help_text="HEX rangi, masalan #FFA07A (ikonka foni uchun)",
    )
    order = models.PositiveIntegerField(default=0, help_text="Tartib raqami")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bo'lim"
        verbose_name_plural = "Bo'limlar"
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

    @property
    def total_questions(self):
        return self.questions.filter(is_active=True).count()


class Question(models.Model):
    """
    Bitta savol. Test ekranida ko'rinadi:
    - rasm (tepada)
    - savol matni ("Qaysi belgi to'xtashni taqiqlaydi?")
    - tushuntirish matni (savol ostida kichik matn)
    - raqamlangan javoblar (3.27, 3.28 va h.k.)
    """
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Savol raqami, masalan 3.27 (test ekranida ko'rinadi)",
    )
    text = models.TextField(help_text="Savol matni")
    description = models.TextField(
        blank=True,
        help_text="Savol ostidagi qo'shimcha tushuntirish matni",
    )
    image = models.ImageField(
        upload_to='questions/',
        null=True, blank=True,
        help_text="Savol rasmi (belgi, rasm va h.k.)",
    )
    explanation = models.TextField(
        blank=True,
        help_text="Javobdan keyin ko'rsatiladigan to'liq tushuntirish",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['section', 'order', 'id']

    def __str__(self):
        return f'[{self.section.name}] {self.text[:60]}'


class Answer(models.Model):
    """
    Savol varianti. Test ekranida: "3.27 To'xtash taqiqlangan".
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Variant raqami, masalan 3.27",
    )
    text = models.CharField(max_length=500, help_text="Variant matni")
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Variant"
        verbose_name_plural = "Variantlar"
        ordering = ['order', 'id']

    def __str__(self):
        mark = '✓' if self.is_correct else '·'
        return f'{mark} {self.number} {self.text[:50]}'


class TestSession(models.Model):
    """
    Foydalanuvchi boshlagan test. Ikki xil rejim:
    - RANDOM: Home ekrandagi "Test boshlash - 20 ta tasodifiy savollar"
    - BY_SECTION: mavzu bo'yicha o'rganish
    - MISTAKES: Home ekrandagi "Xatolarni ko'rish"
    """

    class Mode(models.TextChoices):
        RANDOM = 'random', "Tasodifiy (20 ta savol)"
        BY_SECTION = 'section', "Bo'lim bo'yicha"
        MISTAKES = 'mistakes', "Xatolar ustida ishlash"

    class Status(models.TextChoices):
        ONGOING = 'ongoing', 'Davom etmoqda'
        FINISHED = 'finished', 'Yakunlangan'
        ABANDONED = 'abandoned', 'Tashlab ketilgan'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_sessions')
    section = models.ForeignKey(
        Section, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='test_sessions',
    )
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.RANDOM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING)

    # Savollar ro'yxati (tartib saqlanishi uchun JSON)
    question_ids = models.JSONField(
        default=list,
        help_text="Test boshlanganda tanlangan savol ID lari tartibi bilan",
    )

    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)

    score_percent = models.FloatField(default=0.0, help_text="% ko'rinishidagi natija")

    time_limit_seconds = models.PositiveIntegerField(
        default=1200,
        help_text="Test uchun vaqt chegarasi (sekundda). 20 ta savol = 20 daqiqa",
    )

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Test sessiyasi"
        verbose_name_plural = "Test sessiyalari"
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.full_name} — {self.get_mode_display()} ({self.score_percent}%)'

    def finish(self):
        """Testni yakunlash va natijani hisoblash."""
        answers = self.user_answers.all()
        self.correct_count = answers.filter(is_correct=True).count()
        self.wrong_count = answers.filter(is_correct=False, is_skipped=False).count()
        self.skipped_count = answers.filter(is_skipped=True).count()
        if self.total_questions > 0:
            self.score_percent = round(self.correct_count / self.total_questions * 100, 2)
        self.status = self.Status.FINISHED
        self.finished_at = timezone.now()
        self.save()

    @property
    def time_spent_seconds(self):
        end = self.finished_at or timezone.now()
        return int((end - self.started_at).total_seconds())


class UserAnswer(models.Model):
    """Foydalanuvchining bitta savolga bergan javobi."""
    session = models.ForeignKey(
        TestSession, on_delete=models.CASCADE, related_name='user_answers',
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(
        Answer, on_delete=models.SET_NULL, null=True, blank=True,
    )
    is_correct = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False, help_text="O'tkazib yuborilganmi?")

    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi javobi"
        verbose_name_plural = "Foydalanuvchi javoblari"
        unique_together = [('session', 'question')]
        ordering = ['answered_at']

    def __str__(self):
        return f'{self.session.user.full_name} — {"to\'g\'ri" if self.is_correct else "xato"}'


class UserSectionProgress(models.Model):
    """
    Har bir foydalanuvchining har bir bo'lim bo'yicha progressi.
    Mavzular ekranida "42% umumiy progress" uchun.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_progress')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='user_progress')

    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    mastered_question_ids = models.JSONField(
        default=list,
        help_text="Kamida bir marta to'g'ri javob berilgan savol ID lari",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bo'lim progressi"
        verbose_name_plural = "Bo'limlar progressi"
        unique_together = [('user', 'section')]

    def __str__(self):
        return f'{self.user.full_name} — {self.section.name}: {self.progress_percent}%'

    @property
    def progress_percent(self):
        total = self.section.total_questions
        if total == 0:
            return 0
        mastered = len(self.mastered_question_ids)
        return round(mastered / total * 100, 2)


class MistakeLog(models.Model):
    """
    Xato qilingan savollar. Home ekrandagi "Xatolarni ko'rish" tugmasi uchun.
    Foydalanuvchi to'g'ri javob berganda resolved=True ga o'tadi.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mistakes')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    wrong_count = models.PositiveIntegerField(default=1)
    last_wrong_at = models.DateTimeField(auto_now=True)
    resolved = models.BooleanField(
        default=False,
        help_text="Keyingi urinishda to'g'ri javob berdi",
    )

    class Meta:
        verbose_name = "Xato"
        verbose_name_plural = "Xatolar"
        unique_together = [('user', 'question')]
        ordering = ['-last_wrong_at']

    def __str__(self):
        return f'{self.user.full_name} — {self.question.text[:40]}'
