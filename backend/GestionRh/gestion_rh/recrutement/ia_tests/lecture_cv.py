from pathlib import Path
import pdfplumber

# Chemin relatif correct depuis le fichier `lecture_cv.py`
chemin_pdf = Path(__file__).resolve().parent / 'CV-Donia-Drira-PFE.pdf'

def extraire_texte_cv(path):
    with pdfplumber.open(path) as pdf:
        texte = ''
        for page in pdf.pages:
            texte += page.extract_text()
    return texte

if __name__ == "__main__":
    texte = extraire_texte_cv(chemin_pdf)
    print(texte[:1000])  # Affiche les 1000 premiers caractères
