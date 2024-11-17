from django import forms
from .models import Task, Signature

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to']

class SignatureForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = ['signature_file']
