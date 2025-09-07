from django.urls import path
from . import views

app_name = 'scraping'

urlpatterns = [
    path('dashboard/', views.scraping_dashboard, name='dashboard'),
    path('credentials/', views.credentials_view, name='credentials'),
    path('start/', views.start_scraping_view, name='start_scraping'),
    path('task/<str:task_id>/', views.check_task_status, name='task_status'),
]
