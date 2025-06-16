import os
import joblib
from django.conf import settings

# Chemins vers les fichiers .joblib dans ton dossier ml_model/
model_path = os.path.join(settings.BASE_DIR, 'ml_model/svm_model.joblib')
vectorizer_path = os.path.join(settings.BASE_DIR, 'ml_model/vectorizer.joblib')

# Charger UNE SEULE FOIS
svm_model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)