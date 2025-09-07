from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('courses/', views.courses_view, name='courses'),
    path('assignments/', views.assignments_view, name='assignments'),
    path('settings/', views.account_settings_view, name='account_settings'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
