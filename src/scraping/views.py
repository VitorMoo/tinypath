from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from user.models import UnaerpCredentials
from celery.result import AsyncResult
import json


@login_required
def credentials_view(request):
    """
    View para gerenciar credenciais UNAERP
    """
    user_credentials = None

    try:
        user_credentials = request.user.unaerp_credentials
    except UnaerpCredentials.DoesNotExist:
        pass

    if request.method == 'POST':
        ra = request.POST.get('ra')
        password = request.POST.get('password')

        if ra and password:
            # Criar ou atualizar credenciais
            credentials, created = UnaerpCredentials.objects.get_or_create(
                user=request.user,
                defaults={'ra': ra}
            )

            credentials.ra = ra
            credentials.set_password(password)
            credentials.save()

            if created:
                messages.success(request, 'Credenciais UNAERP criadas com sucesso!')
            else:
                messages.success(request, 'Credenciais UNAERP atualizadas com sucesso!')

            return redirect('scraping:credentials')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')

    context = {
        'credentials': user_credentials,
    }

    return render(request, 'scraping/credentials.html', context)


@login_required
@require_POST
def start_scraping_view(request):
    """
    View para iniciar scraping manual
    """
    try:
        if not hasattr(request.user, 'unaerp_credentials'):
            return JsonResponse({
                'success': False,
                'error': 'Credenciais UNAERP não configuradas'
            })

        print(f"Iniciando scraping para usuário: {request.user.email}")

        from scraping.tasks import scrape_user_data
        task = scrape_user_data.delay(request.user.id)

        print(f"Task criada com ID: {task.id}")

        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': 'Scraping iniciado com sucesso!'
        })

    except Exception as e:
        print(f"Erro no start_scraping_view: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def check_task_status(request, task_id):
    """
    View para verificar status de uma tarefa
    """
    try:
        result = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready(),
        }

        if result.ready():
            if result.successful():
                response_data['result'] = result.result
            else:
                response_data['error'] = str(result.result)

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        })


@login_required
def test_sync_view(request):
    """
    View de teste para sincronização
    """
    return render(request, 'scraping/test_sync.html')


@login_required
def scraping_dashboard(request):
    """
    Dashboard do scraping com estatísticas
    """
    try:
        credentials = request.user.unaerp_credentials
        has_credentials = True
    except UnaerpCredentials.DoesNotExist:
        credentials = None
        has_credentials = False

    from core.models import Course, Assignment

    total_courses = Course.objects.filter(user=request.user).count()
    total_assignments = Assignment.objects.filter(user=request.user).count()
    pending_assignments = Assignment.objects.filter(user=request.user, completed=False).count()

    context = {
        'has_credentials': has_credentials,
        'credentials': credentials,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'pending_assignments': pending_assignments,
    }

    return render(request, 'scraping/dashboard.html', context)
