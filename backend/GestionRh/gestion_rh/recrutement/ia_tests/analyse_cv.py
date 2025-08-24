import os
import pdfplumber
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
import joblib


# Charger le modèle spaCy pour le traitement du texte
nlp = spacy.load("fr_core_news_sm")
    
# extraire les compétences et calculer le score 
def analyser_cv(path_pdf: str, competences_attendues: list[str]) -> float:
    with pdfplumber.open(path_pdf) as pdf:
        texte = ' '.join([page.extract_text() for page in pdf.pages if page.extract_text()])
#nettoyer les mots 
    doc = nlp(texte.lower())
    tokens = [token.lemma_ for token in doc if token.is_alpha]

    texte_cv = " ".join(tokens)
    nb_matchs = sum(1 for comp in competences_attendues if comp.lower() in texte_cv)
#Calcule le pourcentage de compétences présentes dans le CV.
    score = round((nb_matchs / len(competences_attendues)) * 100, 2)
    return score


# Extraire uniquement les compétences d'un CV
def extract_skills_from_cv(path_pdf: str) -> list:
    with pdfplumber.open(path_pdf) as pdf:
        texte = ''.join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Traitement du texte avec spaCy pour extraire les lemmes
    doc = nlp(texte.lower())
    compsesliences = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
    return competences

# Entraîner le modèle SVM (à appeler manuellement une fois)
# cette fonction est faite pour tester manuellement, les données sont statiques 
def train_model():
    cv_paths = [
        "uploads/cv/CV-Donia-Drira-PFE.pdf",
        "uploads/cv/cv_Lobna.pdf"
    ]
    y = [1, 0]

    skills = [extract_skills_from_cv(path) for path in cv_paths]
    skills_text = [" ".join(skill_set) for skill_set in skills]

    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(skills_text)

    model = SVC(kernel='linear')
    model.fit(X, y)

    # ✅ Créer le dossier avant de sauvegarder
    model_dir = os.path.join(os.path.dirname(__file__), '../../ml_model')
    model_dir = os.path.abspath(model_dir)
    os.makedirs(model_dir, exist_ok=True)

    # ✅ Sauvegarder les fichiers .joblib dans le bon dossier
    joblib.dump(model, os.path.join(model_dir, 'svm_model.joblib'))
    joblib.dump(vectorizer, os.path.join(model_dir, 'vectorizer.joblib'))