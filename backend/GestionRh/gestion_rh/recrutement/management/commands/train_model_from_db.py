from django.core.management.base import BaseCommand
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from django.conf import settings
import joblib
import re
import string
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))

def clean_text(text):
    # Suppression des caractères spéciaux, chiffres, ponctuation
    text = re.sub(r'\d+', '', str(text))  # supprime les chiffres
    text = text.translate(str.maketrans('', '', string.punctuation))  # ponctuation
    text = text.lower()
    text = " ".join([word for word in text.split() if word not in STOPWORDS])
    return text.strip()

class Command(BaseCommand):
    help = "Prétraite les données, entraîne un modèle ML et affiche les métriques"

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'gestion_rh', 'dataset', 'dataset_candidats_adapte.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR("❌ Fichier CSV introuvable."))
            return

        df = pd.read_csv(file_path)

        if not {'cv', 'titre', 'description', 'label'}.issubset(df.columns):
            self.stdout.write(self.style.ERROR("❌ Les colonnes nécessaires sont manquantes."))
            return

        # Combinaison des champs texte
        df['text'] = df['cv'].fillna('') + ' ' + df['titre'].fillna('') + ' ' + df['description'].fillna('')
        df['text'] = df['text'].apply(clean_text)

        X = df['text']
        y = df['label']

        # Division en train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Pipeline : TF-IDF + Logistic Regression
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('clf', LogisticRegression(max_iter=1000))
        ])

        # Entraînement
        pipeline.fit(X_train, y_train)

        # Prédiction
        y_pred = pipeline.predict(X_test)

        # Résultats
        self.stdout.write(self.style.SUCCESS("✅ Résultats du modèle :\n"))
        self.stdout.write(classification_report(y_test, y_pred))

        # Sauvegarde du modèle
        model_path = os.path.join(settings.BASE_DIR, 'trained_model.joblib')
        joblib.dump(pipeline, model_path)
        self.stdout.write(self.style.SUCCESS(f"✅ Modèle sauvegardé : {model_path}"))
