from django.core.management.base import BaseCommand
from recrutement.models import Candidature
import pandas as pd
import os
import pdfplumber
import spacy
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import TruncatedSVD
import numpy as np
from datetime import date
from langdetect import detect


SPACY_MODELS = {
    "fr": spacy.load("fr_core_news_sm"),
    "en": spacy.load("en_core_web_sm")
}

# Dictionnaire de correspondance entre niveau d'expérience et valeur numérique
EXPERIENCE_MAPPING = {
    "aucune": 0,
    "moins_1_an": 0.5,
    "entre_1_2_ans": 1.5,
    "entre_2_5_ans": 3.5,
    "entre_5_10_ans": 7.5,
    "plus_10_ans": 12
}

# Extensions de fichiers autorisées
VALID_EXTENSIONS = ['.pdf', '.doc', '.docx']

class Command(BaseCommand):
    help = "Prépare un dataset enrichi pour l'entraînement du modèle IA RH"

    # Fonction de nettoyage du texte
    def nettoyer_texte(self, texte):
        texte = re.sub(r"[^\w\s]", " ", texte)  # Supprimer les caractères spéciaux
        texte = re.sub(r"\s+", " ", texte)        # Supprimer les espaces multiples
        texte = texte.lower().strip()               # Convertir en minuscules et enlever les espaces
        return texte

    # Calculer l'âge à partir de la date de naissance
    def calculate_age(self, birthdate):
        today = date.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

    # Détection simple des CV à deux colonnes
    def detect_two_columns(self, text_pages):
        line_counts = [len(page.splitlines()) for page in text_pages if page]
        average_lines = sum(line_counts) / len(line_counts) if line_counts else 0
        for page in text_pages:
            if page and page.count('\n') > average_lines * 1.5:
                return True
        return False

    def handle(self, *args, **kwargs):
        dataset = []  # Liste pour stocker les données finales

        # Parcours des candidatures analysées avec score disponible
        for c in Candidature.objects.filter(analyse_effectuee=True, score_matching__isnull=False):
            try:
                cv_path = c.candidat.cv.path
                ext = os.path.splitext(cv_path)[1].lower()
                if ext not in VALID_EXTENSIONS:
                    self.stdout.write(self.style.WARNING(f"❌ Format non pris en charge pour {cv_path}"))
                    continue

                # Lecture du contenu texte depuis le fichier PDF
                with pdfplumber.open(cv_path) as pdf:
                    text_pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                    texte = " ".join(text_pages)

                # Refuser les CV trop courts
                if not texte.strip() or len(texte.split()) < 30:
                    self.stdout.write(self.style.WARNING(f"❌ CV vide ou très court : {cv_path}"))
                    continue
                # ✅ Détection mais sans exclusion
                is_two_column = self.detect_two_columns(text_pages)

                # Détection automatique de la langue
                langue_detectee = detect(texte)
                if langue_detectee not in SPACY_MODELS:
                    continue  # Ignorer les langues non supportées

                # Traitement NLP avec le bon modèle
                nlp = SPACY_MODELS[langue_detectee]
                texte_clean = self.nettoyer_texte(texte)
                doc = nlp(texte_clean)
                tokens = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
                texte_final = " ".join(tokens)
                nb_mots = len(tokens)

                # Récupération des métadonnées du candidat
                niveau_etude = c.candidat.niveau_etude or "inconnu"
                niveau_experience = c.candidat.niveau_experience or "aucune"
                age = self.calculate_age(c.candidat.date_naissance) if c.candidat.date_naissance else 0

                # Ajout des données dans la liste
                dataset.append({
                    "texte_cv": texte_final,
                    "nb_mots": nb_mots,
                    "niveau_etude": niveau_etude,
                    "niveau_experience": niveau_experience,
                    "langue": langue_detectee,
                    "age": age,
                    "two_column": int(is_two_column),
                    "label": c.label 
                })

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Erreur pour {c.id}: {e}"))

        if not dataset:
            self.stdout.write(self.style.ERROR("Aucune donnée préparée."))
            return

        # Conversion en DataFrame Pandas
        df = pd.DataFrame(dataset)
        df.drop_duplicates(inplace=True)
        df.dropna(subset=["texte_cv"], inplace=True)

        # Suppression des valeurs aberrantes via IQR
        q1 = df["nb_mots"].quantile(0.25)
        q3 = df["nb_mots"].quantile(0.75)
        iqr = q3 - q1
        df = df[(df["nb_mots"] >= q1 - 1.5 * iqr) & (df["nb_mots"] <= q3 + 1.5 * iqr)]

        # Transformation des variables catégorielles en numériques
        df["experience_val"] = df["niveau_experience"].map(EXPERIENCE_MAPPING).fillna(0)
        df["niveau_etude_encoded"] = LabelEncoder().fit_transform(df["niveau_etude"])
        df["langue_encoded"] = LabelEncoder().fit_transform(df["langue"])

        # Création de nouvelles features (feature engineering)
        df["sum_feat"] = df[["experience_val", "nb_mots"]].sum(axis=1)
        df["diff_feat"] = df["experience_val"] - df["nb_mots"]
        df["avg_feat"] = df[["experience_val", "nb_mots"]].mean(axis=1)
        df["prod_feat"] = df["experience_val"] * df["nb_mots"]
        df["quotient_feat"] = df["experience_val"] / df["nb_mots"].replace(0, 1)

        # Vectorisation TF-IDF du texte + réduction de dimension
        tfidf = TfidfVectorizer(stop_words="english", max_features=100)
        X_text = tfidf.fit_transform(df["texte_cv"])
        svd = TruncatedSVD(n_components=2)
        X_text_reduced = svd.fit_transform(X_text)

        # Standardisation des features numériques
        scaler = StandardScaler()
        features = df[["experience_val", "nb_mots", "age", "sum_feat", "diff_feat", "avg_feat", "prod_feat", "quotient_feat"]]
        features_scaled = scaler.fit_transform(features)

        # Fusion finale : features numériques + texte réduit
        X_final = pd.DataFrame(
            np.hstack((features_scaled, X_text_reduced)),
            columns=[
                "experience_scaled", "nb_mots_scaled", "age_scaled", "sum_feat_scaled",
                "diff_feat_scaled", "avg_feat_scaled", "prod_feat_scaled", "quotient_feat_scaled",
                "text_dim1", "text_dim2"
            ]
        )
        # Ajout des variables encodées et du label
        X_final["niveau_etude"] = df["niveau_etude_encoded"].values
        X_final["langue"] = df["langue_encoded"].values
        X_final["two_column"] = df["two_column"].values
        X_final["label"] = df["label"].values


        # Sauvegarde du fichier CSV final
        os.makedirs("dataset", exist_ok=True)
        X_final.to_csv("dataset/prepared_dataset.csv", index=False)
        self.stdout.write(self.style.SUCCESS("✅ Dataset enrichi sauvegardé dans dataset/prepared_dataset.csv"))
