import requests
import os

# Configuration
API_URL = "http://localhost:8000"
PATIENT_ID = "patient_12345"
FAKE_IRM_FILE = "irm_test.txt"

def print_step(step, msg):
    print(f"\n{'='*10} ÉTAPE {step}: {msg} {'='*10}")

def run_demo():
    # --- PRÉPARATION ---
    # print_step(0, "Préparation (Réinitialisation du consentement)")
    # # On s'assure que le patient a donné son consentement au début de la démo
    # response_grant = requests.post(f"{API_URL}/grant/{PATIENT_ID}")
    # if response_grant.status_code == 200:
    #     print(f"✅ Consentement pour '{PATIENT_ID}' activé.")
    # else:
    #     print(f"⚠️  Impossible de réinitialiser le consentement (Code: {response_grant.status_code}). La démo peut échouer si l'accès était déjà révoqué.")
    
    # On crée un faux fichier médical
    with open(FAKE_IRM_FILE, "w") as f:
        f.write("DONNEES CONFIDENTIELLES: Tumeur bénigne détectée lobe frontal.")
    
    # --- 1. UPLOAD (Simulation Hôpital) ---
    print_step(1, "Envoi d'un dossier médical sécurisé")
    with open(FAKE_IRM_FILE, "rb") as f:
        response = requests.post(f"{API_URL}/upload/{PATIENT_ID}", files={"file": f})
    
    if response.status_code == 200:
        print(f"✅ Succès: {response.json()}")
    else:
        print(f"❌ Erreur Upload: {response.text}")
        os.remove(FAKE_IRM_FILE)
        return

    filename = FAKE_IRM_FILE # Le nom est gardé par l'API

    # --- 2. ACCÈS AUTORISÉ (Simulation IA / Recherche) ---
    print_step(2, "Tentative d'accès par l'IA (Consentement OK)")
    response = requests.get(f"{API_URL}/read/{PATIENT_ID}/{filename}")
    
    if response.status_code == 200:
        print(f"✅ L'IA a lu le fichier déchiffré :")
        print(f"   Contenu: '{response.text}'")
    else:
        print(f"❌ Erreur Lecture: {response.text}")

    # --- 3. RÉVOCATION (Simulation Portail Patient) ---
    print_step(3, "Le patient révoque l'accès via son portail")
    response = requests.post(f"{API_URL}/revoke/{PATIENT_ID}")
    print(f"ℹ️ Action: {response.json()['message']}")

    # --- 4. ACCÈS INTERDIT (Vérification Zero-Trust) ---
    print_step(4, "Nouvelle tentative d'accès par l'IA (Consentement KO)")
    response = requests.get(f"{API_URL}/read/{PATIENT_ID}/{filename}")
    
    if response.status_code == 403:
        print(f"🛡️ SÉCURITÉ ACTIVÉE: L'accès a été bloqué comme prévu !")
        print(f"   Message API: {response.json()['detail']}")
    else:
        print(f"❌ FAILLE DE SÉCURITÉ: L'accès aurait dû être bloqué. Code: {response.status_code}")

    # Nettoyage
    os.remove(FAKE_IRM_FILE)

if __name__ == "__main__":
    run_demo()