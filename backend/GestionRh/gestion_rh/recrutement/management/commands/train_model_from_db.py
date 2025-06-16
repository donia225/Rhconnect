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
        candidats_traités = []

        # 1️⃣ Construire le dataset pour entraînement
        for candidature in Candidature.objects.filter(analyse_effectuee=True, score_matching__isnull=False):
            try:
                cv_path = candidature.candidat.cv.path
                skills = extract_skills_from_cv(cv_path)
                if not skills:
                    continue

                texte = " ".join(skills)
                X_text.append(texte)
                y.append(1 if candidature.score_matching >= 50 else 0)

                # ✅ On garde en mémoire pour appliquer la prédiction après
                candidats_traités.append((candidature, texte))

            except Exception as e:
                self.stdout.write(f"⚠️ Erreur pour la candidature {candidature.id}: {e}")

        if len(X_text) < 2:
            self.stdout.write("❌ Pas assez de données pour entraîner un modèle.")
            return

        # Debug infos
        from collections import Counter
        print("🟡 Données pour entraînement")
        print("Répartition y :", Counter(y))

        # 2️⃣ Entraîner le modèle
        vectorizer = TfidfVectorizer(stop_words='english')
        X_vect = vectorizer.fit_transform(X_text)

        model = SVC(kernel='linear')
        model.fit(X_vect, y)

        # 3️⃣ Sauvegarder le modèle et le vectorizer
        model_dir = os.path.join("ml_model")
        os.makedirs(model_dir, exist_ok=True)

        joblib.dump(model, os.path.join(model_dir, 'svm_model.joblib'))
        joblib.dump(vectorizer, os.path.join(model_dir, 'vectorizer.joblib'))

        self.stdout.write("✅ Modèle IA entraîné et sauvegardé avec succès.")

        # 4️⃣ Mettre à jour la prédiction pour chaque candidature
        for candidature, texte in candidats_traités:
            try:
                vect_input = vectorizer.transform([texte])
                pred = model.predict(vect_input)[0]
                candidature.prediction = "Correspond" if pred == 1 else "Ne correspond pas"
                candidature.save()
                print(f"✅ Candidature {candidature.id} : prédiction sauvegardée → {candidature.prediction}")
            except Exception as e:
                print(f"❌ Erreur de prédiction pour {candidature.id} : {e}")

        self.stdout.write("🎉 Toutes les prédictions ont été mises à jour.")
