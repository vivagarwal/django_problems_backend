from django.urls import path
from . import views

urlpatterns = [
    path('api/get-all-problems/', views.get_all_problems, name='abc'),
    path('api/get-problem-description/<int:id>', views.get_problem_description, name='abc1'),
    path('api/check-solution/<int:id>', views.check_solution, name='abc2'),
    path('api/run', views.run_code, name='abc3'),
    path('api/submit', views.submit_solution, name='abc3'),




]