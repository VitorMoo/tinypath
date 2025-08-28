from django.db import models
from django.conf import settings


class UnaerpCredentials(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ra = models.CharField(max_length=100, verbose_name='RA')
    password = models.CharField(max_length=100, verbose_name='Senha')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Credencial UNAERP'
        verbose_name_plural = 'Credenciais UNAERP'

    def __str__(self):
        return f"UNAERP - {self.user.email} (RA: {self.ra})"
