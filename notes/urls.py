from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.note_list, name='list'),
    path('create/', views.note_create, name='create'),
    path('<int:pk>/', views.note_detail, name='detail'),
    path('<int:pk>/edit/', views.note_edit, name='edit'),
    path('<int:pk>/delete/', views.note_delete, name='delete'),
    path('<int:pk>/summarize/', views.note_ai_summarize, name='summarize'),
    path('<int:pk>/improve/', views.note_ai_improve, name='improve'),
]