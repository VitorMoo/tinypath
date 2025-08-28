from django.db import models
from django.conf import settings
from .courses import Course


class Assignment(models.Model):
    title = models.CharField(max_length=255, verbose_name='Título')
    due_date = models.DateField(verbose_name='Data de Entrega')
    alert_sent = models.BooleanField(default=False, verbose_name='Alerta Enviado')
    alert_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Alerta Enviado em')
    last_checked_at = models.DateTimeField(auto_now=True, verbose_name='Última Verificação')

    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Disciplina')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuário')

    class Meta:
        unique_together = ['title', 'course', 'due_date']
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'

    def __str__(self):
        return f"{self.title} - {self.course.name} ({self.due_date})"
