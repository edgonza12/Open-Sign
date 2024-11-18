from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

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
