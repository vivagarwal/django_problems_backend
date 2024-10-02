from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello_world, name='hello_world'),
    path('hello/<int:id>/', views.hello_id, name='hello_id'),
    path('calculate/', views.calculate, name='calculate'),
]