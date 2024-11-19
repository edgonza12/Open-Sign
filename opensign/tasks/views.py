from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse
from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm, RejectTaskForm
from accounts.models import UserProfile
from .utils import sign_task, verify_signature, generate_task_pdf


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

    # Obtener el perfil del usuario y su llave privada
    user_profile = UserProfile.objects.get(user=request.user)
    private_key = user_profile.private_key

    # Crear la firma digital
    data_to_sign = f"{task.title}|{task.description}"
    signature = sign_task(data_to_sign, private_key)

    # Guardar la firma y aprobar la tarea
    task.signature = signature
    task.is_approved = True
    task.save()

    return redirect('list_tasks')

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
    public_key = user_profile.public_key

    # Preparar los datos para la verificación
    data_to_verify = f"{task.title}|{task.description}"

    # Verificar la firma
    is_valid = verify_signature(data_to_verify, task.signature, public_key)

    # Renderizar el resultado
    return render(request, 'tasks/verify_signature.html', {
        'task': task,
        'is_valid': is_valid,
        'error': None
    })

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