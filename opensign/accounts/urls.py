# accounts/urls.py
from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login-page/", views.login_page, name="login_page"),
    path("verificar-firma/", views.verificar_firma, name="verificar_firma"),
    path("registro/", views.registro, name="registro"),
    path("assign-profile/", views.assign_profile_view, name="assign_profile"),
    path(
        "assign-profile/success/",
        views.assign_profile_success_view,
        name="assign_profile_success",
    ),
    path("home/", views.home_page, name="home_page"),  # URL de la página de inicio
    path(
        "sign-document/", views.sign_document, name="sign_document"
    ),  # URL para firmar documentos
    path(
        "view-signed-documents/",
        views.view_signed_documents,
        name="view_signed_documents",
    ),  # URL para visualizar documentos firmados
    path(
        "download-document/<int:document_id>/",
        views.download_signed_document,
        name="download_signed_document",
    ),  # URL para descargar documento firmado
    path(
        "verify-document/", views.verify_document, name="verify_document"
    ),  # URL para verificar documentos
    path("logout/", views.logout_view, name="logout"),  # URL para cerrar sesión
]
