from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser
from core.models import Course, Assignment


@login_required
def dashboard_view(request):
    # Buscar dados do usuário
    courses = Course.objects.filter(user=request.user)
    assignments = Assignment.objects.filter(course__user=request.user)

    # Calcular estatísticas
    total_courses = courses.count()
    total_assignments = assignments.count()

    # Atividades próximas do vencimento (próximos 7 dias)
    next_week = timezone.now() + timedelta(days=7)
    upcoming_assignments = assignments.filter(
        due_date__isnull=False,
        due_date__lte=next_week,
        due_date__gte=timezone.now()
    ).count()

    context = {
        'user': request.user,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'upcoming_assignments': upcoming_assignments,
        'courses': courses[:5],  # Limitado a 5 para o dashboard
    }
    return render(request, 'user/dashboard.html', context)


@login_required
def courses_view(request):
    """Lista todas as disciplinas do usuário"""
    courses = Course.objects.filter(user=request.user).prefetch_related('assignment_set')

    context = {
        'courses': courses,
        'total_courses': courses.count(),
    }
    return render(request, 'user/courses.html', context)


@login_required
def assignments_view(request):
    """Lista todas as atividades do usuário"""
    assignments = Assignment.objects.filter(course__user=request.user).select_related('course').order_by('-due_date', 'title')

    # Filtros
    course_filter = request.GET.get('course')
    if course_filter:
        assignments = assignments.filter(course__id=course_filter)

    # Separar por status
    assignments_with_due = assignments.filter(due_date__isnull=False)
    assignments_without_due = assignments.filter(due_date__isnull=True)

    # Estatísticas
    now = timezone.now().date()
    overdue = assignments_with_due.filter(due_date__lt=now).count()
    upcoming = assignments_with_due.filter(due_date__gte=now, due_date__lte=now + timedelta(days=7)).count()

    context = {
        'assignments': assignments,
        'assignments_with_due': assignments_with_due,
        'assignments_without_due': assignments_without_due,
        'total_assignments': assignments.count(),
        'overdue_count': overdue,
        'upcoming_count': upcoming,
        'courses': Course.objects.filter(user=request.user),
        'selected_course': course_filter,
    }
    return render(request, 'user/assignments.html', context)


@login_required
def account_settings_view(request):
    """Configurações da conta do usuário"""
    if request.method == 'POST':
        # Atualizar informações pessoais
        if 'update_profile' in request.POST:
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.dias_antecedencia_alerta = int(request.POST.get('dias_antecedencia_alerta', 3))
            request.user.receber_emails = request.POST.get('receber_emails') == 'on'
            request.user.save()
            messages.success(request, 'Perfil atualizado com sucesso!')

        # Atualizar senha
        elif 'update_password' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Senha atual incorreta.')
            elif new_password != confirm_password:
                messages.error(request, 'As novas senhas não coincidem.')
            elif len(new_password) < 8:
                messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                # Re-autenticar após mudança de senha
                user = authenticate(username=request.user.email, password=new_password)
                if user:
                    login(request, user)
                messages.success(request, 'Senha alterada com sucesso!')

        return redirect('account_settings')

    context = {
        'user': request.user,
    }
    return render(request, 'user/account_settings.html', context)
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if email and password:
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'E-mail ou senha inválidos.')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')

    return render(request, 'user/login.html')


@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not all([username, email, first_name, last_name, password1, password2]):
            messages.error(request, 'Por favor, preencha todos os campos.')
        elif password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Já existe um usuário com este nome de usuário.')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Já existe um usuário com este e-mail.')
        else:
            try:
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password1
                )
                messages.success(request, 'Conta criada com sucesso! Faça login para continuar.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Erro ao criar conta: {str(e)}')

    return render(request, 'user/register.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('login')
