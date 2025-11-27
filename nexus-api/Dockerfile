# On part d'une image Python légère
FROM python:3.9-slim

# Dossier de travail dans le conteneur
WORKDIR /app

# On installe les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie tout le code
COPY . .

# On lance l'API sur le port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]