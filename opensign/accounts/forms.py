# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from .models import UserProfile


class DocumentVerificationForm(forms.Form):
    document_file = forms.FileField(label="Subir documento para verificar")


class DocumentUploadForm(forms.Form):
    document_file = forms.FileField(label="Subir documento para firmar")


class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = True
        self.fields["password1"].required = True
        self.fields["password2"].required = True
        # Añadir la clase 'form-control' a cada campo del formulario
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class AssignProfileForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Usuario",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    role = forms.ModelChoiceField(
        queryset=UserProfile.objects.values_list("role", flat=True).distinct(),
        label="Perfil",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super(AssignProfileForm, self).__init__(*args, **kwargs)
        self.fields["user"].widget.attrs.update(
            {"placeholder": "Selecciona un usuario"}
        )
        self.fields["role"].widget.attrs.update({"placeholder": "Selecciona un perfil"})

    def assign_profile(self):
        user = self.cleaned_data["user"]
        role = self.cleaned_data["role"]

        # Verifica si el usuario ya tiene un perfil
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        user_profile.role = role  # Asigna el rol
        user_profile.save()

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        role = cleaned_data.get("role")

        if UserProfile.objects.filter(user=user, role=role).exists():
            raise ValidationError("Este usuario ya tiene el perfil asignado.")
