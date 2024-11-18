from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def sign_task(data, private_key_pem):
    """
    Firma los datos de la tarea con la llave privada.
    """
    private_key = RSA.import_key(private_key_pem)
    hashed_data = SHA256.new(data.encode('utf-8'))
    signature = pkcs1_15.new(private_key).sign(hashed_data)
    return signature

def verify_signature(data, signature, public_key_pem):
    """
    Verifica la firma de los datos con la llave pública.
    """
    public_key = RSA.import_key(public_key_pem)
    hashed_data = SHA256.new(data.encode('utf-8'))
    try:
        pkcs1_15.new(public_key).verify(hashed_data, signature)
        return True
    except (ValueError, TypeError):
        return False

def generate_task_pdf(task, user_profile):
    """
    Genera un PDF con los datos de la tarea y la firma digital.
    :param task: Objeto de la tarea.
    :param user_profile: Perfil del usuario con la llave pública.
    :return: BytesIO con el contenido del PDF.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Tarea {task.title}")

    # Título
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 750, f"Tarea: {task.title}")

    # Descripción
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 720, f"Descripción: {task.description}")

    # Asignado a
    assigned_to = task.assigned_to.username if task.assigned_to else "Sin asignar"
    pdf.drawString(100, 690, f"Asignada a: {assigned_to}")

    # Estado de aprobación
    pdf.drawString(100, 660, "Estado: Aprobada")

    # Firma digital
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(100, 630, "Firma Digital:")
    pdf.setFont("Courier", 8)
    signature_preview = str(task.signature)[:100] + "..."  # Muestra los primeros 100 caracteres
    pdf.drawString(100, 610, signature_preview)

    # Información del firmante
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 580, "Llave Pública del Firmante:")
    pdf.setFont("Courier", 8)
    public_key_preview = user_profile.public_key[:100] + "..."  # Muestra los primeros 100 caracteres
    pdf.drawString(100, 560, public_key_preview)

    # Finaliza y guarda
    pdf.save()
    buffer.seek(0)
    return buffer