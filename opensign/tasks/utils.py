from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
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
    Genera un PDF con los datos de la tarea, su estado y comentario de rechazo si aplica.
    :param task: Objeto de la tarea.
    :param user_profile: Perfil del usuario con la llave pública.
    :return: BytesIO con el contenido del PDF.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Tarea {task.title}")

    # Dimensiones de la página
    width, height = letter

    # Encabezado
    pdf.setFillColor(colors.HexColor("#004d40"))  # Verde oscuro
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(1 * inch, height - 1 * inch, "Informe de Tarea")
    pdf.setStrokeColor(colors.HexColor("#004d40"))
    pdf.setLineWidth(2)
    pdf.line(1 * inch, height - 1.1 * inch, width - 1 * inch, height - 1.1 * inch)

    # Subtítulo
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(1 * inch, height - 1.5 * inch, "Detalles de la tarea")

    # Caja de información
    pdf.setFillColor(colors.HexColor("#e8f5e9"))  # Verde claro
    pdf.rect(1 * inch, height - 5 * inch, width - 2 * inch, 3.3 * inch, fill=True, stroke=False)

    # Contenido de la tarea
    pdf.setFillColor(colors.black)  # Texto negro
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(1.2 * inch, height - 2 * inch, "Título:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(2.2 * inch, height - 2 * inch, task.title)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(1.2 * inch, height - 2.5 * inch, "Descripción:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(2.2 * inch, height - 2.5 * inch, task.description)

    assigned_to = task.assigned_to.username if task.assigned_to else "Sin asignar"
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(1.2 * inch, height - 3 * inch, "Asignada a:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(2.2 * inch, height - 3 * inch, assigned_to)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(1.2 * inch, height - 3.5 * inch, "Estado:")
    status_text = "Aprobada" if task.is_approved else "Rechazada"
    pdf.setFont("Helvetica", 12)
    pdf.drawString(2.2 * inch, height - 3.5 * inch, status_text)

    if not task.is_approved and task.rejection_comment:
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, height - 4 * inch, "Comentario de Rechazo:")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(1 * inch, height - 4.3 * inch, task.rejection_comment)

    # Firma digital (solo si está aprobada)
    if task.is_approved:
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, height - 5.5 * inch, "Firma Digital:")
        pdf.setFont("Courier", 10)
        signature_preview = str(task.signature)[:100] + "..." if task.signature else "Sin firma"
        pdf.drawString(1 * inch, height - 5.8 * inch, signature_preview)

        # Llave pública
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, height - 6.3 * inch, "Llave Pública del Firmante:")
        pdf.setFont("Courier", 10)
        public_key_preview = user_profile.public_key[:100] + "..."
        pdf.drawString(1 * inch, height - 6.6 * inch, public_key_preview)

    # Pie de página
    pdf.setFillColor(colors.HexColor("#004d40"))
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(1 * inch, 0.5 * inch, "Generado automáticamente - Sistema de Gestión de Tareas Open Sign")

    # Guardar y retornar el archivo
    pdf.save()
    buffer.seek(0)
    return buffer