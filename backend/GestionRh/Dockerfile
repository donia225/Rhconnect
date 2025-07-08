

FROM python:3.10-slim
WORKDIR /app

# Copie le fichier requirements.txt AVANT
COPY ../requirements.txt ./requirements.txt

# Installe pip + dépendances
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copie tout le reste (code source)
COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
