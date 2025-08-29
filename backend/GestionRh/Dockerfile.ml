FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# Installer dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Installer les dépendances ML
COPY requirements-ml.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-ml.txt

RUN python -m spacy download fr_core_news_sm && python -m spacy validate

# Copier ton code
COPY . .

# Démarrer le worker ML (exemple)
CMD ["python", "-m", "ml_worker"]
