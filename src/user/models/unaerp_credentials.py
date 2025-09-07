from django.db import models
from django.conf import settings
from django.utils import timezone


class UnaerpCredentials(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='unaerp_credentials')
    ra = models.CharField(max_length=100, verbose_name='RA')
    encrypted_password = models.TextField(verbose_name='Senha Criptografada', default='')
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name='Última Sincronização')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Credencial UNAERP'
        verbose_name_plural = 'Credenciais UNAERP'

    def __str__(self):
        return f"UNAERP - {self.user.email} (RA: {self.ra})"

    def set_password(self, raw_password):
        """
        Criptografa e salva a senha
        """
        from scraping.unaerp_scraper import CredentialsManager
        self.encrypted_password = CredentialsManager.encrypt_password(raw_password)

    def check_password(self, raw_password):
        """
        Verifica se a senha está correta
        """
        try:
            from scraping.unaerp_scraper import CredentialsManager
            decrypted = CredentialsManager.decrypt_password(self.encrypted_password)
            return decrypted == raw_password
        except:
            return False

    def get_decrypted_password(self):
        """
        Retorna a senha descriptografada
        """
        from scraping.unaerp_scraper import CredentialsManager
        return CredentialsManager.decrypt_password(self.encrypted_password)

    def needs_sync(self):
        """
        Verifica se precisa fazer sync (última sync foi há mais de 1 hora)
        """
        if not self.last_sync:
            return True

        from datetime import timedelta
        return timezone.now() - self.last_sync > timedelta(hours=1)
