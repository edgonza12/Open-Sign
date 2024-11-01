# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login-page/', views.login_page, name='login_page'),
    path('home/', views.home_page, name='home_page'),  # URL de la página de inicio
    path('sign-document/', views.sign_document, name='sign_document'),  # URL para firmar documentos
    path('view-signed-documents/', views.view_signed_documents, name='view_signed_documents'),  # URL para visualizar documentos firmados
    path('download-document/<int:document_id>/', views.download_signed_document, name='download_signed_document'),  # URL para descargar documento firmado
    path('logout/', views.logout_view, name='logout'),  # URL para cerrar sesión
]
