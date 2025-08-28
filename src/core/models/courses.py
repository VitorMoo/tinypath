from django.db import models
from django.conf import settings


class Course(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nome')
    instructor = models.CharField(max_length=255, verbose_name='Professor')
    link = models.URLField(max_length=500, verbose_name='Link')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuário')

    class Meta:
        unique_together = ('user', 'name')
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        return self.name
