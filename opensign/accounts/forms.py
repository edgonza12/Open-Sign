# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class DocumentVerificationForm(forms.Form):
    document_file = forms.FileField(label="Subir documento para verificar")

class DocumentUploadForm(forms.Form):
    document_file = forms.FileField(label="Subir documento PDF para firmar")

class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir la clase 'form-control' a cada campo del formulario
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'