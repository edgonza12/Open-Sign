from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_task, name="create_task"),
    path("", views.list_tasks, name="list_tasks"),
    path("approve/<int:task_id>/", views.approve_task, name="approve_task"),
    path("reject_task/<int:task_id>/", views.reject_task, name="reject_task"),
    path(
        "verify_task/<int:task_id>/",
        views.verify_task_signature,
        name="verify_task_signature",
    ),
    path(
        "download_task/<int:task_id>/",
        views.download_task_pdf,
        name="download_task_pdf",
    ),
    path("task/reject/<int:task_id>/", views.reject_task, name="reject_task"),
]
