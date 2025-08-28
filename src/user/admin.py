from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin para o modelo de usuário personalizado"""

    list_display = ('email', 'first_name', 'last_name', 'is_active', 'has_unaerp_credentials', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'receber_emails', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informações Pessoais', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Credenciais UNAERP', {
            'fields': ('unaerp_login', 'unaerp_password'),
            'description': 'Credenciais para acesso ao portal da UNAERP'
        }),
        ('Preferências', {
            'fields': ('dias_antecedencia_alerta', 'receber_emails')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')

    def has_credenciais_unaerp(self, obj):
        """Exibe se o usuário tem credenciais da UNAERP configuradas"""
        return obj.has_credenciais_unaerp()
    has_credenciais_unaerp.boolean = True
    has_credenciais_unaerp.short_description = 'Credenciais UNAERP'
