
# Create your views here.
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Signature
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Credenciales inválidas'})
    return JsonResponse({'status': 'error', 'message': 'Solicitud no válida'})


def login_page(request):
    return render(request, 'accounts/login.html')

@login_required
def home_page(request):
    return render(request, 'accounts/home.html')

def logout_view(request):
    logout(request)
    return redirect('login_page')

# accounts/views.py


@login_required
def sign_document(request):
    if request.method == 'POST':
        document_name = request.POST.get('document_name')
        document_file = request.FILES.get('document_file')  # Recibir archivo
        authorize_task = request.POST.get('authorize_task') == 'on'

        if document_file:
            document_content = document_file.read()  # Leer contenido del archivo en bytes

            # Generar claves RSA para el usuario (simulación)
            key = RSA.generate(2048)
            private_key = key
            public_key = key.publickey()

            # Crear el hash del documento
            h = SHA256.new(document_content)

            # Firmar el documento con la clave privada
            signature = pkcs1_15.new(private_key).sign(h)

            # Guardar la firma y la autorización en la base de datos
            Signature.objects.create(
                user=request.user,
                document_name=document_name,
                document_file=document_file,
                signed_document=signature,
                authorized_task=authorize_task
            )

            messages.success(request, "El documento ha sido firmado y la tarea ha sido autorizada.")
            return redirect('home_page')
        else:
            messages.error(request, "Debe seleccionar un archivo para firmar.")

    return render(request, 'accounts/sign_document.html')


@login_required
def view_signed_documents(request):
    # Filtrar los documentos firmados por el usuario actual
    signed_documents = Signature.objects.filter(user=request.user)
    return render(request, 'accounts/view_signed_documents.html', {'signed_documents': signed_documents})


@login_required
def download_signed_document(request, document_id):
    # Obtener el documento firmado por ID y verificar que pertenece al usuario actual
    signed_document = get_object_or_404(Signature, id=document_id, user=request.user)

    # Verificar si el documento tiene un archivo adjunto
    if signed_document.document_file:
        try:
            # Retornar el archivo como respuesta
            response = FileResponse(signed_document.document_file.open('rb'), as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{signed_document.document_file.name}"'
            return response
        except FileNotFoundError:
            raise Http404("El archivo no fue encontrado.")
    else:
        raise Http404("No hay un archivo firmado disponible para este documento.")
    
    # accounts/views.py
@login_required
def view_signed_documents(request):
    signed_documents = Signature.objects.filter(user=request.user)
    return render(request, 'accounts/view_signed_documents.html', {'signed_documents': signed_documents})
