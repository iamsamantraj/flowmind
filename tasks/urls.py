from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('create/', views.task_create, name='create'),
    path('<int:pk>/', views.task_detail, name='detail'),
    path('<int:pk>/edit/', views.task_edit, name='edit'),
    path('<int:pk>/delete/', views.task_delete, name='delete'),
    path('<int:pk>/toggle/', views.task_toggle_status, name='toggle'),
    path('<int:pk>/subtasks/', views.task_ai_subtasks, name='subtasks'),
    path('<int:pk>/prioritize/', views.task_ai_prioritize, name='prioritize'),
]