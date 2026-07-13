from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.chat_home, name='chat'),
    path('new/', views.conversation_new, name='new'),
    path('<int:pk>/', views.conversation_detail, name='conversation'),
    path('<int:pk>/send/', views.conversation_send, name='send'),
    path('<int:pk>/delete/', views.conversation_delete, name='delete'),
]