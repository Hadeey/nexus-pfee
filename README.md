## 1. La Philosophie du Projet : Pourquoi NEXUS ?

Face à la méfiance des établissements de santé européens envers les géants du cloud américains (Cloud Act), NEXUS propose une alternative : **une forteresse numérique souveraine**.

Notre architecture repose sur trois piliers fondamentaux imposés par le cahier des charges :

1.  **Souveraineté des Données :** Contrairement à AWS ou Azure, nos données ne quittent jamais notre infrastructure. Nous utilisons une solution "Self-Hosted" (Hébergée en interne).
2.  **Zero-Trust (Zéro Confiance) :** L'identité ne suffit pas. Chaque accès à une donnée est vérifié en temps réel, conditionné par le consentement actif du patient.
3.  **Security by Design :** La sécurité n'est pas une option. Les données sont chiffrées **avant** même d'être stockées.

---

## 2. Architecture Technique (Les Briques LEGO)

NEXUS n'est pas une application monolithique, mais une architecture **micro-services** orchestrée par Docker. Voici les 4 composants clés qui interagissent dans notre réseau virtuel.

### 🧠 1. Le Cerveau : L'API NEXUS (Python / FastAPI)
C'est le seul composant "fait maison". Il agit comme un **proxy de sécurité intelligent**.
* **Rôle :** C'est le gardien du temple. Aucune requête n'atteint le stockage ou la base de données sans passer par lui.
* **Fonctions Clés :**
    * **Chiffrement à la volée :** Chiffre les fichiers (AES-256) en mémoire vive avant l'écriture sur disque.
    * **Déchiffrement conditionnel :** Ne déchiffre le fichier que si le consentement est valide dans la base de données.
    * **Journalisation (Logging) :** Trace chaque action pour l'audit HDS.

### 📦 2. Le Coffre-Fort : MinIO (Stockage Objet S3)
* **Rôle :** Remplace Amazon S3. C'est ici que sont stockés les fichiers lourds (Imagerie médicale, PDF).
* **Souveraineté :** Logiciel Open-Source installé sur nos serveurs.
* **Sécurité :** Ce stockage est "aveugle". Il ne contient que des fichiers binaires chiffrés. Si un attaquant vole les disques durs, les données sont inexploitable (charabia illisible).

### 📝 3. Le Notaire : PostgreSQL (Base de Données)
* **Rôle :** Mémoire administrative du système.
* **Données stockées :**
    * Table `consentements` : État juridique de l'accès (Patient X = OUI/NON).
    * Table `logs` : Historique des accès (Qui a fait quoi et quand).
* **Séparation des données :** Il ne contient *jamais* les données médicales brutes, uniquement des métadonnées.

### 🐳 4. Le Conteneur : Docker & Docker Compose
* **Rôle :** Standardisation. Il permet de déployer l'architecture complète (API + DB + S3) sur n'importe quel serveur (Linux, Mac, Windows) en une seule commande, garantissant la portabilité du PoC.

---

## 3. Scénarios & Flux de Données (Le "Storytelling")

Voici comment décrire le fonctionnement du système dans le rapport et lors de la soutenance.

### 🔒 Scénario A : L'Upload Sécurisé (Chiffrement à la Source)
*Répond à l'exigence : "Stockage sécurisé avec chiffrement automatique"*

1.  **Envoi :** Le médecin envoie une IRM via l'API.
2.  **Traitement :** L'API reçoit le fichier en mémoire RAM.
3.  **Chiffrement :** Immédiatement, l'algorithme AES transforme le fichier en format chiffré.
4.  **Stockage :** L'API envoie ce fichier chiffré vers le bucket `sante-data` de MinIO.
5.  **Preuve :** Sur le disque dur, le fichier est illisible sans la clé gérée par l'API.

### 🤖 Scénario B : L'Accès IA (Le Zero-Trust en action)
*Répond à l'exigence : "Déploiement sécurisé d'un modèle IA"*

1.  **Demande :** Une IA (ou un chercheur) demande l'accès au fichier du Patient X.
2.  **Vérification 1 (Identité) :** L'API vérifie le token d'accès.
3.  **Vérification 2 (Consentement) :** L'API interroge PostgreSQL : *"Le consentement est-il actif ?"*.
    * *Si OUI :* L'API récupère le fichier chiffré, le déchiffre à la volée, et l'envoie.
    * *Si NON :* L'API renvoie une erreur 403 Forbidden. L'IA n'a aucun accès au fichier.

### 🚫 Scénario C : La Révocation (Conformité RGPD)
*Répond à l'exigence : "API de gestion des consentements / Portail Patient"*

1.  **Action :** Le patient clique sur "Révoquer l'accès" dans son portail.
2.  **Mise à jour :** L'API passe le flag `consent_given` à `FALSE` dans PostgreSQL.
3.  **Effet Immédiat :** Toute tentative d'accès future par l'IA sera bloquée instantanément (voir Scénario B). C'est la garantie du "Droit au retrait" du RGPD.

---

## 4. Arguments Clés pour la Soutenance (Cheat Sheet)

Utilisez ces termes pour valoriser le travail technique :

* **Chiffrement Symétrique (AES-256) :** Choisi pour sa robustesse et sa rapidité sur les gros volumes de données (Imagerie).
* **Indépendance Technologique :** L'utilisation de MinIO prouve que l'architecture est compatible S3 (standard mondial) sans dépendre d'Amazon (Cloud Act).
* **Principe de Moindre Privilège :** Le service de stockage ne connaît pas les clés de déchiffrement. La base de données ne connaît pas le contenu des fichiers.
* **Architecture Modulaire :** Grâce aux micro-services, on peut remplacer le moteur de base de données ou de stockage sans réécrire tout le code.

---

## 5. Guide Rapide (Quick Start)

Pour lancer le Proof of Concept (PoC) sur votre machine :

**Prérequis :** Docker Desktop installé.

1.  **Démarrer l'infrastructure :**
    ```bash
    docker-compose up --build
    ```
    *L'API sera accessible sur `http://localhost:8000` et la console MinIO sur `http://localhost:9001`.*

2.  **Lancer la démo complète (Upload -> IA -> Révocation -> Blocage) :**
    ```bash
    python scripts_demo/demo_complete.py
    ```

3.  **Arrêter et nettoyer :**
    ```bash
    docker-compose down
    ```