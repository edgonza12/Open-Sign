from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from .models import Task
from .forms import TaskForm, RejectTaskForm
from accounts.models import UserProfile
from .utils import sign_task, verify_signature, generate_task_pdf
import base64
from PyPDF2 import PdfReader

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            return redirect('list_tasks')
    else:
        form = TaskForm()
    return render(request, 'tasks/create_task.html', {'form': form})

@login_required
def list_tasks(request):
    tasks = Task.objects.all()
    return render(request, 'tasks/list_tasks.html', {'tasks': tasks})

@login_required
def approve_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Obtener el perfil del usuario y su clave privada
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        private_key_data = user_profile.private_key
        if not private_key_data:
            messages.error(request, "No se ha encontrado una clave privada para tu cuenta.")
            return redirect('list_tasks')
    except UserProfile.DoesNotExist:
        messages.error(request, "No se ha encontrado el perfil de usuario.")
        return redirect('list_tasks')

    # Convertir la clave privada a formato bytes si es necesario
    if isinstance(private_key_data, str):
        private_key_data = private_key_data.encode('utf-8')
    
    # Importar la clave privada
    try:
        private_key = RSA.import_key(private_key_data)
    except Exception as e:
        messages.error(request, f"Error al importar la clave privada: {e}")
        return redirect('list_tasks')

    # Crear el contenido a firmar
    data_to_sign = f"{task.title}|{task.description}".encode('utf-8')

    # Crear el hash del contenido
    try:
        hash_obj = SHA256.new(data_to_sign)
    except Exception as e:
        messages.error(request, f"Error al crear el hash de la tarea: {e}")
        return redirect('list_tasks')
    
    # Firmar el hash
    try:
        signature = pkcs1_15.new(private_key).sign(hash_obj)
    except Exception as e:
        messages.error(request, f"Error al firmar la tarea: {e}")
        return redirect('list_tasks')

    # Crear el contenido firmado
    signed_content = data_to_sign + b'\n---SIGNATURE---\n' + signature

    # Guardar la firma y aprobar la tarea
    try:
        task.signature = signed_content
        task.is_approved = True
        task.save()
        messages.success(request, "Tarea aprobada y firmada exitosamente.")
    except Exception as e:
        messages.error(request, f"Error al guardar la tarea aprobada: {e}")

    return redirect('list_tasks')


# def approve_task(request, task_id):
#     task = get_object_or_404(Task, id=task_id)

#     # Obtener el perfil del usuario y su llave privada
#     user_profile = UserProfile.objects.get(user=request.user)
#     private_key = user_profile.private_key

#     # Crear la firma digital
#     data_to_sign = f"{task.title}|{task.description}"
#     signature = sign_task(data_to_sign, private_key)

#     # Guardar la firma y aprobar la tarea
#     task.signature = signature
#     task.is_approved = True
#     task.save()

#     return redirect('list_tasks')

@login_required
def reject_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        form = RejectTaskForm(request.POST, instance=task)
        if form.is_valid():
            task.is_rejected = True
            task.is_approved = False  # Marcar como rechazada
            form.save()
            return redirect('list_tasks')
    else:
        form = RejectTaskForm(instance=task)

    return render(request, 'tasks/reject_task.html', {'form': form, 'task': task})

@login_required
def verify_task_signature(request, task_id):
    # Obtener la tarea por su ID
    task = get_object_or_404(Task, id=task_id)

    # Verificar que la tarea esté aprobada y tenga una firma
    if not task.is_approved or not task.signature:
        return render(request, 'tasks/verify_signature.html', {
            'task': task,
            'is_valid': False,
            'error': "La tarea no está aprobada o no tiene una firma registrada."
        })

    # Obtener la llave pública del usuario que aprobó la tarea
    assigned_user = task.assigned_to
    user_profile = get_object_or_404(UserProfile, user=assigned_user)
    public_key_data = user_profile.public_key
    if not public_key_data:
        return render(request, 'tasks/verify_signature.html', {
            'task': task,
            'is_valid': False,
            'error': "No se ha encontrado una clave pública para este usuario."
        })

    # Convertir la clave pública a formato RSA
    try:
        public_key = RSA.import_key(public_key_data)
    except Exception as e:
        return render(request, 'tasks/verify_signature.html', {
            'task': task,
            'is_valid': False,
            'error': f"Error al importar la clave pública: {e}"
        })

    # Separar el contenido firmado
    try:
        # Separar el contenido firmado por el delimitador ---SIGNATURE---
        signed_data, signature = task.signature.split(b'\n---SIGNATURE---\n')

        # Verificar la firma
        hash_obj = SHA256.new(signed_data)
        try:
            pkcs1_15.new(public_key).verify(hash_obj, signature)
            is_valid = True
        except (ValueError, TypeError):
            is_valid = False
    except Exception as e:
        return render(request, 'tasks/verify_signature.html', {
            'task': task,
            'is_valid': False,
            'error': f"Error al verificar la firma: {e}"
        })

    # Renderizar el resultado
    return render(request, 'tasks/verify_signature.html', {
        'task': task,
        'is_valid': is_valid,
        'error': None
    })


# def verify_task_signature(request, task_id):
#     # Obtener la tarea por su ID
#     task = get_object_or_404(Task, id=task_id)

#     # Verificar que la tarea esté aprobada y tenga una firma
#     if not task.is_approved or not task.signature:
#         return render(request, 'tasks/verify_signature.html', {
#             'task': task,
#             'is_valid': False,
#             'error': "La tarea no está aprobada o no tiene una firma registrada."
#         })

#     # Obtener la llave pública del usuario que aprobó la tarea
#     assigned_user = task.assigned_to
#     user_profile = get_object_or_404(UserProfile, user=assigned_user)
#     public_key = user_profile.public_key

#     # Preparar los datos para la verificación
#     data_to_verify = f"{task.title}|{task.description}"

#     # Verificar la firma
#     is_valid = verify_signature(data_to_verify, task.signature, public_key)

#     # Renderizar el resultado
#     return render(request, 'tasks/verify_signature.html', {
#         'task': task,
#         'is_valid': is_valid,
#         'error': None
#     })

def download_task_pdf(request, task_id):
    # Obtener la tarea
    task = get_object_or_404(Task, id=task_id)

    # Obtener el perfil del usuario asignado (si lo hay)
    user_profile = (
        get_object_or_404(UserProfile, user=task.assigned_to)
        if task.assigned_to
        else None
    )

    # Generar el PDF
    pdf_buffer = generate_task_pdf(task, user_profile)

    # Retornar como respuesta de archivo
    response = FileResponse(pdf_buffer, as_attachment=True, filename=f"Tarea_{task.id}.pdf")
    return response