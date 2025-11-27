import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Configuration DB (les mêmes valeurs que dans docker-compose)
DB_HOST = "db"
DB_NAME = "nexus_db"
DB_USER = "nexus_user"
DB_PASS = "db_password"

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
    """Crée la table des consentements au démarrage."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Table simple : patient_id et statut du consentement (True/False)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS consentements (
            patient_id VARCHAR(50) PRIMARY KEY,
            consent_given BOOLEAN DEFAULT TRUE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def check_consent(patient_id: str) -> bool:
    """Vérifie si un patient a donné son accord."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT consent_given FROM consentements WHERE patient_id = %s", (patient_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    # Si le patient n'existe pas encore, on considère qu'il consent par défaut (pour le PoC)
    if result is None:
        return True 
    return result[0]

def revoke_consent(patient_id: str):
    """Révoque l'accès (Action du portail patient)."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Upsert : Met à jour si existe, sinon insère
    cur.execute("""
        INSERT INTO consentements (patient_id, consent_given)
        VALUES (%s, FALSE)
        ON CONFLICT (patient_id) DO UPDATE SET consent_given = FALSE;
    """, (patient_id,))
    conn.commit()
    cur.close()
    conn.close()