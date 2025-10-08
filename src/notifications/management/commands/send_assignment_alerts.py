from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from core.models import Assignment
from user.models import CustomUser


class Command(BaseCommand):
    help = 'Envia e-mails de alerta para atividades próximas do vencimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem enviar e-mails (apenas mostra o que seria enviado)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Envia apenas para um usuário específico (ID)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        user_id = options.get('user_id')

        self.stdout.write(self.style.SUCCESS('Iniciando envio de alertas de atividades...'))

        users = CustomUser.objects.filter(receber_emails=True)

        if user_id:
            users = users.filter(id=user_id)

        total_emails_sent = 0
        total_users_notified = 0

        for user in users:
            # Buscar atividades pendentes do usuário
            today = timezone.now().date()
            alert_days = user.dias_antecedencia_alerta or 3
            alert_date = today + timedelta(days=alert_days)

            # Buscar atividades não concluídas com vencimento dentro do período de alerta
            assignments = Assignment.objects.filter(
                user=user,
                completed=False,
                due_date__isnull=False,
                due_date__gte=today,
                due_date__lte=alert_date,
                alert_sent=False  # Não enviar se já foi enviado alerta
            ).select_related('course').order_by('due_date')

            if not assignments.exists():
                self.stdout.write(
                    f'  Usuário {user.email}: Sem atividades para alertar'
                )
                continue

            # Calcular dias até o vencimento para cada atividade
            assignments_with_days = []
            for assignment in assignments:
                days_until_due = (assignment.due_date - today).days
                assignment.days_until_due = days_until_due
                assignments_with_days.append(assignment)

            # Preparar contexto do e-mail
            context = {
                'user': user,
                'assignments': assignments_with_days,
                'site_url': 'http://localhost:8000/dashboard/',
                'settings_url': 'http://localhost:8000/dashboard/settings/',
            }

            html_message = render_to_string('emails/assignment_alert.html', context)
            text_message = render_to_string('emails/assignment_alert.txt', context)

            subject = f'UnaTrack: {len(assignments)} atividade{"s" if len(assignments) > 1 else ""} próxima{"s" if len(assignments) > 1 else ""} do vencimento'

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'  [DRY RUN] Enviaria e-mail para {user.email}')
                )
                self.stdout.write(f'    Assunto: {subject}')
                self.stdout.write(f'    Atividades: {len(assignments)}')
                for assignment in assignments_with_days:
                    self.stdout.write(
                        f'      - {assignment.title} ({assignment.days_until_due} dias)'
                    )
            else:
                try:
                    # Enviar e-mail
                    send_mail(
                        subject=subject,
                        message=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                    assignments.update(
                        alert_sent=True,
                        alert_sent_at=timezone.now()
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ E-mail enviado para {user.email}')
                    )
                    self.stdout.write(f'    Atividades alertadas: {len(assignments)}')

                    total_emails_sent += 1
                    total_users_notified += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Erro ao enviar e-mail para {user.email}: {str(e)}')
                    )

        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: {total_users_notified} e-mails seriam enviados')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Processo concluído!')
            )
            self.stdout.write(f'   Total de e-mails enviados: {total_emails_sent}')
            self.stdout.write(f'   Total de usuários notificados: {total_users_notified}')
