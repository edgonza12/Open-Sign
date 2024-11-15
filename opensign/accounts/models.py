# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Signature(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signatures')
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='signed_documents/')  # Archivo del documento
    signed_document = models.BinaryField(null=True, blank=True)  # Firma del documento
    authorized_task = models.BooleanField(default=False)  # Estado de autorización de la tarea\
    timestamp = models.DateTimeField(auto_now_add=True)  # Fecha y hora de la firma

    def __str__(self):
        return f"Signature for {self.document_name} by {self.user.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    private_key = models.TextField(blank=True, null=True)  #  Clave privada del usuario
    public_key = models.TextField(blank=True, null=True)   # Clave pública del usuario
    def __str__(self):
        return self.user.username