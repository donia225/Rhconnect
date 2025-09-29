
# 1. Image de base (Python 3.10)
FROM python:3.10-slim

# Configuration des variables d'environnement pour Python et le chemin d'accès
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# LIGNE CRITIQUE 1 : S'assure que Python cherche bien dans le répertoire /app
ENV PYTHONPATH /app

# LIGNE CRITIQUE 2 : Définition explicite du chemin complet vers les settings.py
# Ceci force Django à trouver la configuration du projet
ENV DJANGO_SETTINGS_MODULE="gestion_rh.settings"

# 2. Installation des dépendances du système (pour PostgreSQL)
# Nécessaire pour psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    ca-certificates \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 3. Installation des dépendances Python
# Installer les dépendances en premier pour profiter du cache Docker
COPY requirements.txt .
COPY requirements-ml.txt .

# Mise à jour de pip et installation des dépendances
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-ml.txt

# 4. Copie du code de l'application
# Copie tous les fichiers depuis le dossier GestionRh vers /app
COPY . .

# Configuration du port pour Cloud Run
ENV PORT 8080
EXPOSE $PORT

# 5. Point d'entrée du conteneur (Utilisation de Gunicorn)
# Chemin complet qui a fonctionné pour charger le wsgi, avant l'erreur de BDD
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
