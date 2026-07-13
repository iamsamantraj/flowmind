from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goal_list, name='list'),
    path('create/', views.goal_create, name='create'),
    path('<int:pk>/', views.goal_detail, name='detail'),
    path('<int:pk>/edit/', views.goal_edit, name='edit'),
    path('<int:pk>/delete/', views.goal_delete, name='delete'),
    path('<int:pk>/progress/', views.goal_update_progress, name='progress'),
    path('<int:pk>/coaching/', views.goal_ai_coaching, name='coaching'),
    path('<int:pk>/milestones/', views.goal_ai_milestones, name='milestones'),
]