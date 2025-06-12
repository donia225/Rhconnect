from django.core.management.base import BaseCommand
from recrutement.models import Candidature
from recrutement.ia_tests.analyse_cv import extract_skills_from_cv

import os
import joblib
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC

class Command(BaseCommand):
    help = "Entraîne automatiquement le modèle SVM depuis les candidatures analysées"

    def handle(self, *args, **kwargs):
        self.stdout.write("📦 Entraînement du modèle IA en cours...")

        nlp = spacy.load("fr_core_news_sm")

        X_text = []
        y = []

        for candidature in Candidature.objects.filter(analyse_effectuee=True, score_matching__isnull=False):
            try:
                cv_path = candidature.candidat.cv.path
                skills = extract_skills_from_cv(cv_path)
                if not skills:
                    continue

                texte = " ".join(skills)
                X_text.append(texte)

                y.append(1 if candidature.score_matching >= 50 else 0)
            except Exception as e:
                self.stdout.write(f"⚠️ Erreur pour la candidature {candidature.id}: {e}")

        if len(X_text) < 2:
            self.stdout.write("❌ Pas assez de données pour entraîner un modèle.")
            return
          # ✅ Affichage temporaire pour debug
        print("🟡 Données pour entraînement")
        print("y =", y)
        print("X_text =", X_text)
        from collections import Counter
        print("Répartition y :", Counter(y))

        vectorizer = TfidfVectorizer(stop_words='english')
        X_vect = vectorizer.fit_transform(X_text)

        model = SVC(kernel='linear')
        model.fit(X_vect, y)

        model_dir = os.path.join("ml_model")
        os.makedirs(model_dir, exist_ok=True)

        joblib.dump(model, os.path.join(model_dir, 'svm_model.joblib'))
        joblib.dump(vectorizer, os.path.join(model_dir, 'vectorizer.joblib'))

        self.stdout.write("✅ Modèle IA entraîné et sauvegardé avec succès.")
