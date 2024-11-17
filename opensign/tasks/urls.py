from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_task, name='create_task'),
    path('', views.list_tasks, name='list_tasks'),
    path('approve/<int:task_id>/', views.approve_task, name='approve_task'),
]
