from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm 
from accounts.models import UserProfile
from .utils import sign_task, verify_signature


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

#@login_required
# def approve_task(request, task_id):
#     task = get_object_or_404(Task, id=task_id)
#     if request.method == 'POST':
#         form = SignatureForm(request.POST, request.FILES)
#         if form.is_valid():
#             signature = form.save(commit=False)
#             signature.task = task
#             signature.signed_by = request.user
#             signature.save()
#             task.is_approved = True
#             task.save()
#             return redirect('list_tasks')
#     else:
#         form = SignatureForm()
#     return render(request, 'tasks/approve_task.html', {'task': task, 'form': form})
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

def reject_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.is_rejected = True
    task.is_approved = False  # Por si la tarea ya estaba aprobada
    task.save()
    return redirect('list_tasks')  # Redirige a la lista de tareas


def verify_task_signature(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    user_profile = UserProfile.objects.get(user=task.assigned_to)
    public_key = user_profile.public_key

    data_to_verify = f"{task.title}|{task.description}"
    is_valid = verify_signature(data_to_verify, task.signature, public_key)

    context = {
        'task': task,
        'is_valid': is_valid,
    }
    return render(request, 'tasks/verify_signature.html', context)