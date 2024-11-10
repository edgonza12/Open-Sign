
# Create your views here.
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Signature
from .forms import DocumentVerificationForm, DocumentUploadForm
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from .utils import sign_pdf  # Importa la función de firma
import os

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
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document_file = request.FILES['document_file']
            user = request.user

            # Verificar y crear la carpeta temporal si no existe
            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Guardar temporalmente el archivo PDF subido en el directorio temporal
            temp_path = os.path.join(temp_dir, document_file.name)
            with open(temp_path, 'wb') as temp_file:
                for chunk in document_file.chunks():
                    temp_file.write(chunk)

            # Verificar y crear la carpeta de documentos firmados si no existe
            signed_dir = "signed_documents"
            if not os.path.exists(signed_dir):
                os.makedirs(signed_dir)

            # Definir la ruta de salida del PDF firmado
            signed_path = os.path.join(signed_dir, document_file.name)

            # Firmar el documento usando la clave privada del usuario
            user_private_key = user.private_key  # Supone que la clave privada está en el modelo User
            signature = sign_pdf(temp_path, signed_path, user_private_key, user.id)

            if signature:
                # Guardar la firma en la base de datos
                Signature.objects.create(
                    user=user,
                    document_name=document_file.name,
                    signed_document=signature,
                    authorized_task=True
                )

                # Eliminar el archivo temporal después de firmar
                os.remove(temp_path)

                messages.success(request, f"Documento firmado exitosamente y guardado en {signed_path}")
                return redirect('document_list')  # Redirige a la lista de documentos
            else:
                messages.error(request, "Hubo un error al intentar firmar el documento.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)  # Eliminar el archivo temporal si existe
        else:
            messages.error(request, "Hubo un error con el formulario. Intenta de nuevo.")
    
    else:
        form = DocumentUploadForm()
    
    return render(request, 'accounts/sign_document.html', {'form': form})

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
def verify_document(request):
    if request.method == 'POST':
        form = DocumentVerificationForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Procesa el archivo subido
            document_file = request.FILES.get('document_file')  # Obtener archivo
            if document_file is None:
                messages.error(request, "No se ha subido ningún archivo. Intenta de nuevo.")
                return render(request, 'accounts/verify_document.html', {'form': form})

            document_content = document_file.read()  # Leer el contenido del archivo

            # Generar el hash del documento subido
            uploaded_hash = SHA256.new(document_content)
            
            # Buscar documentos firmados con el mismo nombre en la base de datos
            matched_documents = Signature.objects.filter(document_name=document_file.name)
            if not matched_documents:
                messages.error(request, "No se encontraron documentos que coincidan.")
                return render(request, 'accounts/verify_document.html', {'form': form})

            # Iterar a través de los documentos firmados que coincidan para verificar la firma
            for signed_doc in matched_documents:
                try:
                    # Suponiendo que tenemos la clave pública del usuario en el modelo `Signature`
                    public_key = RSA.import_key(signed_doc.user.public_key)

                    # Verificar la firma
                    pkcs1_15.new(public_key).verify(uploaded_hash, signed_doc.signed_document)
                    
                    # Mensaje de éxito indicando quién firmó y si la tarea fue autorizada
                    messages.success(
                        request,
                        f"El documento ha sido firmado por {signed_doc.user.username} y la tarea fue {'autorizada' if signed_doc.authorized_task else 'no autorizada'}."
                    )
                    break  # Detener el bucle si se encuentra una coincidencia
                except (ValueError, TypeError):
                    # Si la verificación falla para este documento
                    continue
            else:
                # Si ningún documento coincide tras iterar todos
                messages.error(request, "La firma del documento no coincide con ninguna firma registrada.")
        else:
            messages.error(request, "Hubo un error con el formulario. Intenta de nuevo.")
    
    else:
        form = DocumentVerificationForm()

    return render(request, 'accounts/verify_document.html', {'form': form})


def sign_pdf(document_path, output_path, private_key, user_id):
    # Leer el archivo PDF
    doc = fitz.open(document_path)

    # Agregar una marca visual en la última página indicando que fue firmado
    page = doc[-1]  # Última página
    text = f"Document signed by user {user_id}"
    rect = fitz.Rect(50, 50, 200, 100)  # Posición de la marca en el PDF
    page.insert_textbox(rect, text, fontsize=12, color=(0, 0, 0))

    # Guardar el PDF marcado
    doc.save(output_path)
    doc.close()

    # Calcular el hash del documento firmado
    with open(output_path, "rb") as f:
        pdf_content = f.read()
    document_hash = SHA256.new(pdf_content)

    # Generar la firma digital con la clave privada
    private_key = RSA.import_key(private_key)
    signature = pkcs1_15.new(private_key).sign(document_hash)

    return signature  # Devuelve la firma para almacenarla o verificarla luego

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Loguea al usuario tras registrarse
            return redirect('home')  # Redirige a la página de inicio
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})