from cryptography.fernet import Fernet

# Dans un vrai projet, cette clé est dans un coffre-fort (Vault).
# Pour le PoC, on la génère ou on la fixe via une variable d'env.
KEY = Fernet.generate_key() 
cipher = Fernet(KEY)

def encrypt_data(data: bytes) -> bytes:
    """Chiffre les données brutes."""
    return cipher.encrypt(data)

def decrypt_data(data: bytes) -> bytes:
    """Déchiffre les données pour l'utilisateur autorisé."""
    return cipher.decrypt(data)