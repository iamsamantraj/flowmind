from django.urls import path
from . import views
from .jwt_views import (
    JWTLoginView, JWTLogoutView,
    JWTRefreshView, JWTRegisterView, WhoAmIView
)

app_name = 'api'

urlpatterns = [
    # ── JWT Auth endpoints ──
    path('auth/login/', JWTLoginView.as_view(), name='jwt-login'),
    path('auth/register/', JWTRegisterView.as_view(), name='jwt-register'),
    path('auth/logout/', JWTLogoutView.as_view(), name='jwt-logout'),
    path('auth/refresh/', JWTRefreshView.as_view(), name='jwt-refresh'),
    path('auth/me/', WhoAmIView.as_view(), name='whoami'),

    # ── Dashboard ──
    path('stats/', views.DashboardStatsView.as_view(), name='stats'),

    # ── Notes ──
    path('notes/', views.NoteListCreateView.as_view(), name='note-list'),
    path('notes/<int:pk>/', views.NoteDetailView.as_view(), name='note-detail'),
    path('notes/<int:pk>/summarize/', views.NoteAISummarizeView.as_view(), name='note-summarize'),

    # ── Tasks ──
    path('tasks/', views.TaskListCreateView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:pk>/subtasks/', views.TaskAISubtasksView.as_view(), name='task-subtasks'),

    # ── Goals ──
    path('goals/', views.GoalListCreateView.as_view(), name='goal-list'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    path('goals/<int:pk>/advice/', views.GoalAIAdviceView.as_view(), name='goal-advice'),

    # ── Profile ──
    path('profile/', views.UserProfileView.as_view(), name='profile'),
]