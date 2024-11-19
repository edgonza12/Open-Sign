from django import forms
from .models import Task
from django.contrib.auth.models import User

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to']

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),  # Lista de usuarios
        widget=forms.Select(attrs={'class': 'form-select'}),  # Clase de Bootstrap
        required=True, 
        label="Asignar a"
    )

class RejectTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['rejection_comment']
        labels = {'rejection_comment': 'Motivo del rechazo'}
        widgets = {
            'rejection_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe el motivo del rechazo aquí...',
                'rows': 4,
            }),
        }