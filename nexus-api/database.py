import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import datetime

# Configuration DB via Variables d'Environnement
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "nexus_db")
DB_USER = os.getenv("DB_USER", "nexus_user")
DB_PASS = os.getenv("DB_PASS", "db_password")

def get_db_connection():
    """Crée une connexion à la base de données. Réessaie si la DB n'est pas prête."""
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
            )
            return conn
        except psycopg2.OperationalError:
            print("La base de données n'est pas encore prête... on attend 2s")
            time.sleep(2)

def init_db():
    """Crée les tables nécessaires (Consentements + Logs) au démarrage."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Table Consentements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS consentements (
            patient_id VARCHAR(50) PRIMARY KEY,
            consent_given BOOLEAN DEFAULT TRUE
        );
    """)
    
    # 2. Table Logs (Traçabilité / Audit)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            patient_id VARCHAR(50),
            action VARCHAR(50),
            requester VARCHAR(50),
            status VARCHAR(20),
            details TEXT
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("[INIT] Base de données initialisée (Consentements & Logs).")

def check_consent(patient_id: str) -> bool:
    """Vérifie si un patient a donné son accord."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT consent_given FROM consentements WHERE patient_id = %s", (patient_id,))
        result = cur.fetchone()
        cur.close()
    finally:
        conn.close()
    
    # Si le patient n'existe pas encore, on considère qu'il consent par défaut (pour le PoC)
    if result is None:
        return True 
    return result[0]

def revoke_consent(patient_id: str):
    """Révoque l'accès (Action du portail patient)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Upsert : Met à jour si existe, sinon insère
        cur.execute("""
            INSERT INTO consentements (patient_id, consent_given)
            VALUES (%s, FALSE)
            ON CONFLICT (patient_id) DO UPDATE SET consent_given = FALSE;
        """, (patient_id,))
        conn.commit()
        cur.close()
    finally:
        conn.close()

def log_action(patient_id: str, action: str, requester: str, status: str, details: str = ""):
    """Enregistre une action dans les logs pour audit."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO access_logs (patient_id, action, requester, status, details)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, action, requester, status, details))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[ERROR] Impossible d'écrire le log : {e}")
    finally:
        conn.close()

def get_logs(limit: int = 50):
    """Récupère les derniers logs pour l'UI."""
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM access_logs 
            ORDER BY timestamp DESC 
            LIMIT %s
        """, (limit,))
        logs = cur.fetchall()
        cur.close()
        return logs
    finally:
        conn.close()