from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .models import CustomUser


@csrf_protect
def login_view(request):
    """View para login do usuário"""
    if request.user.is_authenticated:
        return redirect('#')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if email and password:
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', '#')
                return redirect(next_url)
            else:
                messages.error(request, 'E-mail ou senha inválidos.')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')

    return render(request, 'user/login.html')


@csrf_protect
def register_view(request):
    """View para cadastro de usuário"""
    if request.user.is_authenticated:
        return redirect('#')

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
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Já existe um usuário com este e-mail.')
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Já existe um usuário com este nome de usuário.')
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
    """View para logout do usuário"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('login')
