# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from .models import UserProfile

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
        self.fields['username'].required = True
        self.fields['password1'].required = True
        self.fields['password2'].required = True
        # Añadir la clase 'form-control' a cada campo del formulario
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class AssignProfileForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Usuario",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),  # Cambia aquí para obtener instancias de Group
        label="Perfil",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def assign_profile(self):
        user = self.cleaned_data['user']
        role = self.cleaned_data['role']  # Esto será una instancia de Group

        # Obtener o crear el perfil de usuario
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        user_profile.role = role  # Asignar la instancia de Group
        user_profile.save()