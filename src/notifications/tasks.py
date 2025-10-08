from celery import shared_task
from django.core.management import call_command


@shared_task(name='notifications.send_assignment_alerts')
def send_assignment_alerts():
    """
    Task Celery para enviar alertas de atividades próximas do vencimento.
    """
    call_command('send_assignment_alerts')
    return 'Alertas de atividades enviados com sucesso'
