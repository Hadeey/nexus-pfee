from fastapi import FastAPI, UploadFile, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from security import encrypt_data, decrypt_data
import boto3
import os
from contextlib import asynccontextmanager
from database import init_db, check_consent, revoke_consent, log_action, get_logs

# Configuration
S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "nexus_admin")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "azerty123")
API_TOKEN = os.getenv("API_TOKEN", "secure-token-123") # Pour le PoC

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Vérifie le token d'accès (IAM basique)."""
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide")
    return credentials.credentials

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialiser la DB (Consentements + Logs)
    init_db()
    
    # 2. Initialiser le Bucket S3 (Stockage)
    try:
        s3.create_bucket(Bucket='sante-data')
        print("[INIT] Bucket 'sante-data' créé avec succès.")
    except Exception as e:
        print(f"[INFO] Vérification Bucket : {e}") 
    yield
    print("[SHUTDOWN] Fermeture.")

app = FastAPI(lifespan=lifespan)

# CORS pour l'UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En prod, restreindre à l'URL du front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion MinIO
s3 = boto3.client('s3', endpoint_url=S3_ENDPOINT, 
                  aws_access_key_id=S3_ACCESS_KEY, 
                  aws_secret_access_key=S3_SECRET_KEY)

@app.get("/logs", deps=[Depends(verify_token)])
def read_audit_logs():
    return get_logs()

@app.post("/upload/{patient_id}", deps=[Depends(verify_token)])
async def upload_medical_record(patient_id: str, file: UploadFile, token: str = Depends(verify_token)):
    user_id = "Medecin_X" # Dans un vrai IAM, on extrairait l'identité du token
    
    # 1. LOGGING : Trace de la tentative
    log_action(patient_id, "UPLOAD_ATTEMPT", user_id, "PENDING", f"Fichier: {file.filename}")
    
    try:
        # 2. CHIFFREMENT À LA SOURCE
        content = await file.read()
        encrypted_content = encrypt_data(content)
        
        # 3. STOCKAGE SÉCURISÉ
        s3.put_object(Bucket='sante-data', Key=f"{patient_id}/{file.filename}", Body=encrypted_content)
        
        # LOGGING SUCCESS
        log_action(patient_id, "UPLOAD_SUCCESS", user_id, "SUCCESS", f"Taille: {len(content)} bytes")
        return {"status": "securely stored", "file": file.filename}
    
    except Exception as e:
        log_action(patient_id, "UPLOAD_ERROR", user_id, "ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/read/{patient_id}/{filename}", deps=[Depends(verify_token)])
def read_medical_record(patient_id: str, filename: str):
    user_id = "AI_Model_Y" # Simulé
    
    # 1. VÉRIFICATION CONSENTEMENT (Zero-Trust)
    if not check_consent(patient_id):
        log_action(patient_id, "READ_DENIED", user_id, "DENIED", "Consentement révoqué")
        raise HTTPException(status_code=403, detail="Accès révoqué par le patient")

    try:
        # 2. RÉCUPÉRATION & DÉCHIFFREMENT
        encrypted_file = s3.get_object(Bucket='sante-data', Key=f"{patient_id}/{filename}")
        decrypted_content = decrypt_data(encrypted_file['Body'].read())
        
        # 3. LOGGING SUCCESS
        log_action(patient_id, "READ_SUCCESS", user_id, "SUCCESS", f"Fichier: {filename}")
        
        return decrypted_content
        
    except Exception as e:
        log_action(patient_id, "READ_ERROR", user_id, "ERROR", str(e))
        raise HTTPException(status_code=500, detail="Erreur accès fichier ou clé invalide")

@app.post("/revoke/{patient_id}", deps=[Depends(verify_token)])
def revoke_access(patient_id: str):
    user_id = "Patient_Portail"
    revoke_consent(patient_id)
    log_action(patient_id, "REVOKE_CONSENT", user_id, "SUCCESS", "Accès révoqué via API")
    return {"message": f"Accès révoqué pour le patient {patient_id}."}