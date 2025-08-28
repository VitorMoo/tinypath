from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='E-mail')
    first_name = models.CharField(max_length=30, verbose_name='Nome')
    last_name = models.CharField(max_length=30, verbose_name='Sobrenome')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    dias_antecedencia_alerta = models.IntegerField(default=2, verbose_name='Dias de antecedência para alerta')
    receber_emails = models.BooleanField(default=True, verbose_name='Receber e-mails')

    USERNAME_FIELD = 'email'  # Login será feito com e-mail
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def complete_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def has_unaerp_credentials(self):
        """Verifica se o usuário tem credenciais da UNAERP configuradas"""
        try:
            return hasattr(self, 'unaerpcredentials') and self.unaerpcredentials is not None
        except:
            return False
