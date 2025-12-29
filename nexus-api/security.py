```python
import os
import base64
from cryptography.fernet import Fernet

# Récupération de la clé depuis l'environnement pour la persistance
# Si aucune clé n'est fournie, on en génère une (ATTENTION: Danger pour la prod si redémarrage)
env_key = os.getenv("ENCRYPTION_KEY")

if env_key:
    # On s'assure qu'elle est en bytes
    try:
        KEY = env_key.encode()
        # Validation simple (Fernet attend 32 url-safe base64-encoded bytes)
        Fernet(KEY) 
    except Exception as e:
        print(f"[CRITICAL] Clé d'environnement invalide : {e}. Génération d'une nouvelle clé (Données précédentes perdues).")
        KEY = Fernet.generate_key()
else:
    print("[WARNING] Pas de variable ENCRYPTION_KEY. Génération d'une clé volatile (Données perdues au redémarrage).")
    KEY = Fernet.generate_key()

cipher = Fernet(KEY)

def encrypt_data(data: bytes) -> bytes:
    """Chiffre les données brutes."""
    return cipher.encrypt(data)

def decrypt_data(data: bytes) -> bytes:
    """Déchiffre les données pour l'utilisateur autorisé."""
    return cipher.decrypt(data)
```