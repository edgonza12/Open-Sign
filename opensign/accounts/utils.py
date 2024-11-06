import fitz  # PyMuPDF
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

def sign_pdf(document_path, output_path, private_key, user_id):
    try:
        # Leer el archivo PDF
        doc = fitz.open(document_path)

        # Agregar una marca visual en la última página indicando que fue firmado
        page = doc[-1]  # Última página
        text = f"Document signed by user {user_id}"
        rect = fitz.Rect(50, 50, 200, 100)  # Posición de la marca en el PDF
        page.insert_textbox(rect, text, fontsize=12, color=(0, 0, 0))

        # Guardar el PDF marcado
        doc.save(output_path)
        doc.close()

        # Calcular el hash del documento firmado
        with open(output_path, "rb") as f:
            pdf_content = f.read()
        document_hash = SHA256.new(pdf_content)

        # Generar la firma digital con la clave privada
        private_key = RSA.import_key(private_key)
        signature = pkcs1_15.new(private_key).sign(document_hash)

        return signature  # Devuelve la firma para almacenarla o verificarla luego
    except Exception as e:
        print(f"Error en el proceso de firma: {e}")
        return None
