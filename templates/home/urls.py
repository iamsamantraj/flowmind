from django.urls import path
from . import views

urlpatterns = [
    path('Home',views.Home),
    path('about',views.about),
]