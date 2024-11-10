from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Signature(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Asociado al usuario
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='signed_documents/')  # Archivo del documento
    signed_document = models.BinaryField(null=True, blank=True)  # Firma del documento
    authorized_task = models.BooleanField(default=False)  # Estado de autorización de la tarea\
    timestamp = models.DateTimeField(auto_now_add=True)  # Fecha y hora de la firma

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    private_key = models.TextField(blank=True, null=True)  # Almacena la clave privada en formato PEM

    def __str__(self):
        return f"Firma de {self.user.username} en {self.document_name}"
        return self.user.username

