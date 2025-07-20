"""
encryption.py
Shared encryption utilities for Presentation Clicker.
"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_fernet(pwd: str) -> Fernet:
    """
    Derives a Fernet encryption key from the password using PBKDF2HMAC.
    
    Args:
        pwd: Password string.
        
    Returns:
        Fernet: Fernet encryption object.
    """
    salt = b"presentationclicker_salt"  # Use a constant salt or store per-room for more security
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(pwd.encode("utf-8")))
    return Fernet(key)
