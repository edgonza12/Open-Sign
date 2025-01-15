
# Create your views here.
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Signature, UserProfile
from .forms import DocumentVerificationForm, DocumentUploadForm, RegistroForm, AssignProfileForm
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from .utils import sign_pdf, role_required  # Importa la función de firma
import os, hashlib

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

#@role_required('Admin')
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
            
            # Obtener el perfil del usuario y la clave privada
            try:
                profile = UserProfile.objects.get(user=user)
                private_key_data = profile.private_key
                if not private_key_data:
                    messages.error(request, "No se ha encontrado una clave privada para tu cuenta.")
                    return redirect('sign_document')
            except UserProfile.DoesNotExist:
                messages.error(request, "No se ha encontrado el perfil de usuario.")
                return redirect('sign_document')

            # Convertir private_key_data a bytes si es necesario
            if isinstance(private_key_data, str):
                private_key_data = private_key_data.encode('utf-8')
            
            # Intento de importar la clave privada en formato bytes
            try:
                private_key = RSA.import_key(private_key_data)
            except Exception as e:
                messages.error(request, f"Error al importar la clave privada: {e}")
                return redirect('sign_document')

            # Guardar el archivo subido en bytes
            doc_data = document_file.read()
            if not isinstance(doc_data, bytes):
                messages.error(request, "Error al leer el archivo en formato de bytes.")
                return redirect('sign_document')

            # Crear hash del documento
            try:
                hash_obj = SHA256.new(doc_data)
            except Exception as e:
                messages.error(request, f"Error al crear el hash del documento: {e}")
                return redirect('sign_document')
            
            # Intentar firmar el hash
            try:
                signature = pkcs1_15.new(private_key).sign(hash_obj)
            except Exception as e:
                messages.error(request, f"Error al firmar el documento: {e}")
                return redirect('sign_document')

            # Crear contenido del documento firmado
            signed_content = doc_data + b'\n---SIGNATURE---\n' + signature

            # Usar ContentFile para envolver los datos binarios
            signed_file = ContentFile(signed_content, name=f"signed_{document_file.name}")

            # Registrar la firma en la base de datos
            try:
                Signature.objects.create(
                    user=user,
                    document_name=document_file.name,
                    document_file=signed_file,
                    signed_document = signed_content,  
                    authorized_task=True
                )
                
                messages.success(request, "Documento firmado exitosamente.")
                return redirect('sign_document')
            except Exception as e:
                messages.error(request, f"Error al guardar el documento firmado: {e}")
                return redirect('sign_document')
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
    if request.method == 'POST' and 'document_file' in request.FILES:
        document_file = request.FILES['document_file']
        try:
            # Leer el contenido del archivo
            file_content = document_file.read()

            # Verificar si contiene el delimitador
            if file_content.count(b'\n---SIGNATURE---\n') != 1:
                messages.error(request, "El archivo no contiene un formato válido de firma digital.")
                return render(request, 'accounts/verify_document.html')

            # Separar contenido y firma
            content, signature = file_content.split(b'\n---SIGNATURE---\n')

            # Calcular el hash del contenido
            hash_obj = SHA256.new(content)

            # Recuperar la clave pública del usuario
            user = request.user
            profile = user.userprofile  # Asegúrate de que UserProfile esté relacionado con User
            public_key_data = profile.public_key

            if isinstance(public_key_data, str):
                public_key_data = public_key_data.encode('utf-8')

            public_key = RSA.import_key(public_key_data)

            # Verificar la firma
            try:
                pkcs1_15.new(public_key).verify(hash_obj, signature)
                messages.success(request, "El documento se verificó correctamente. La firma es válida.")
            except (ValueError, TypeError):
                messages.error(request, "La firma no es válida o el documento ha sido alterado.")
        except Exception as e:
            messages.error(request, f"Error al procesar el documento: {e}")

    return render(request, 'accounts/verify_document.html')



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
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Generar clave privada y pública RSA
            key = RSA.generate(2048)
            private_key = key.export_key().decode('utf-8')  # Clave privada en formato string
            public_key = key.publickey().export_key().decode('utf-8')  # Clave pública en formato string

            # Crear perfil de usuario con claves
            UserProfile.objects.create(
                user=user,
                private_key=private_key,
                public_key=public_key
            )

            # Loguear al usuario tras registrarse
            login(request, user)
            return redirect('login_page')  # Redirige a la página de inicio
    else:
        form = RegistroForm()
    
    return render(request, 'accounts/registro.html', {'form': form})

def assign_role(user, role_name):
    try:
        role = Group.objects.get(name=role_name)
        user.groups.add(role)
        user.userprofile.role = role
        user.userprofile.save()
    except Group.DoesNotExist:
        raise ValueError(f"El rol '{role_name}' no existe.")
    
@login_required
def assign_profile_view(request):
    if request.method == 'POST':
        form = AssignProfileForm(request.POST)
        if form.is_valid():
            form.assign_profile()
            return redirect('assign_profile_success')  # Redirige a la nueva vista
    else:
        form = AssignProfileForm()

    return render(request, 'assign_profile.html', {'form': form})


@login_required
def assign_profile_success_view(request):
    return render(request, 'assign_profile_succes.html')


def verificar_firma(request):
    datos_firma = None
    error = None

    if request.method == 'POST' and 'document_file' in request.FILES:
        document_file = request.FILES['document_file']
        try:
            # Leer el contenido del archivo cargado
            contenido = document_file.read()

            # Dividir el contenido original y la firma usando el separador
            try:
                contenido_original, firma = contenido.split(b'\n---SIGNATURE---\n')
            except ValueError:
                raise ValueError("El archivo no contiene una firma válida.")

            # Calcular el hash del contenido original
            hash_obj = SHA256.new(contenido_original)

            # Buscar coincidencias en la base de datos de `Signature`
            firmas_registradas = Signature.objects.all()
            firma_valida = False

            for firma_registrada in firmas_registradas:
                # Obtener los datos binarios del archivo firmado desde la base de datos
                firmado_data = firma_registrada.signed_document

                if not firmado_data:  # Validar si firmado_data no es None
                    continue

                # Separar contenido y firma del documento almacenado
                try:
                    contenido_almacenado, firma_almacenada = firmado_data.split(b'\n---SIGNATURE---\n')
                except ValueError:
                    continue  # Si el formato no es válido, pasa al siguiente registro

                # Verificar si el contenido original coincide con el almacenado
                if contenido_original != contenido_almacenado:
                    continue

                # Obtener la clave pública del usuario que firmó el documento
                try:
                    user_profile = UserProfile.objects.get(user=firma_registrada.user)
                    llave_publica = RSA.import_key(user_profile.public_key.encode('utf-8'))
                except UserProfile.DoesNotExist:
                    continue  # Si el perfil no existe, pasa al siguiente registro

                # Intentar verificar la firma
                try:
                    pkcs1_15.new(llave_publica).verify(hash_obj, firma)
                    firma_valida = True
                    datos_firma = {
                        'nombre_archivo': firma_registrada.document_name,
                        'firmante': firma_registrada.user.username,
                        'fecha_firma': firma_registrada.timestamp,
                    }
                    break  # Documento válido, detener búsqueda
                except (ValueError, TypeError):
                    continue

            if not firma_valida:
                error = "La firma no es válida o no coincide con ningún registro."

        except Exception as e:
            error = f"Error al procesar el documento: {e}"

    return render(request, 'accounts/verificar_firma.html', {
        'datos_firma': datos_firma,
        'error': error
    })
