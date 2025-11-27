from fastapi import FastAPI, UploadFile, HTTPException, Depends
from security import encrypt_data, decrypt_data
import boto3 # Pour parler à MinIO
from contextlib import asynccontextmanager
from database import init_db, check_consent, revoke_consent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialiser la DB (Consentements)
    init_db()
    
    # 2. Initialiser le Bucket S3 (Stockage)
    try:
        s3.create_bucket(Bucket='sante-data')
        print("[INIT] Bucket 'sante-data' créé avec succès.")
    except Exception as e:
        # Si le bucket existe déjà, MinIO peut renvoyer une erreur, on l'ignore ou on vérifie.
        # Pour le PoC, on suppose que s'il y a une erreur, c'est qu'il existe peut-être déjà.
        print(f"[INFO] Vérification Bucket : {e}")
        
    yield
    print("[SHUTDOWN] Fermeture des ressources si nécessaire.")
    db.close()

app = FastAPI(lifespan=lifespan)

# Connexion à MinIO (votre stockage interne)
s3 = boto3.client('s3', endpoint_url='http://minio:9000', 
                  aws_access_key_id='nexus_admin', 
                  aws_secret_access_key='azerty123')

@app.post("/upload/{patient_id}")
async def upload_medical_record(patient_id: str, file: UploadFile):
    # 1. LOGGING : On trace qui fait quoi 
    print(f"[LOG] Tentative d'upload pour le patient {patient_id}")
    
    # 2. CHIFFREMENT À LA SOURCE [cite: 29]
    content = await file.read()
    encrypted_content = encrypt_data(content)
    
    # 3. STOCKAGE SÉCURISÉ
    # On envoie le fichier chiffré dans MinIO. 
    # Même si un hacker vole le disque dur, les fichiers sont illisibles.
    s3.put_object(Bucket='sante-data', Key=f"{patient_id}/{file.filename}", Body=encrypted_content)
    
    return {"status": "securely stored", "file": file.filename}

@app.get("/read/{patient_id}/{filename}")
def read_medical_record(patient_id: str, filename: str):
    # 1. VÉRIFICATION CONSENTEMENT (Zero-Trust)
    # On imagine une fonction check_consent() qui interroge la DB
    if not check_consent(patient_id):
        # Si le patient a révoqué l'accès via son portail :
        raise HTTPException(status_code=403, detail="Accès révoqué par le patient")

    # 2. RÉCUPÉRATION & DÉCHIFFREMENT
    encrypted_file = s3.get_object(Bucket='sante-data', Key=f"{patient_id}/{filename}")
    decrypted_content = decrypt_data(encrypted_file['Body'].read())
    
    # 3. LOGGING D'ACCÈS
    print(f"[LOG] Donnée accédée pour patient {patient_id}")
    
    return decrypted_content

@app.post("/revoke/{patient_id}")
def revoke_access(patient_id: str):
    revoke_consent(patient_id)
    return {"message": f"Accès révoqué pour le patient {patient_id}. Les données sont verrouillées."}