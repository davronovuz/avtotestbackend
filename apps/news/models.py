from django.db import models


class News(models.Model):
    title = models.CharField(max_length=255, help_text="Yangilik sarlavhasi")
    description = models.TextField(help_text="Yangilik matni")
    image = models.ImageField(
        upload_to='news/',
        null=True, blank=True,
        help_text="Yangilik rasmi (ixtiyoriy)",
    )
    author = models.CharField(
        max_length=150,
        blank=True,
        help_text="Muallif ismi (ixtiyoriy)",
    )
    is_published = models.BooleanField(default=True, help_text="Chop etilganmi?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Yangilik"
        verbose_name_plural = "Yangiliklar"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
