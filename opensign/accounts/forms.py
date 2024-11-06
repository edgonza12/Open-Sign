# accounts/forms.py
from django import forms

class DocumentVerificationForm(forms.Form):
    document_file = forms.FileField(label="Subir documento para verificar")

class DocumentUploadForm(forms.Form):
    document_file = forms.FileField(label="Subir documento PDF para firmar")