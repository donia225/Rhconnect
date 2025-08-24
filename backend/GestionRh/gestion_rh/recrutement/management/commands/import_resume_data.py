import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from recrutement.models import User, Candidat, OffreEmploi, Candidature

def map_experience(years):
    if years == 0:
        return 'aucune'
    elif years < 1:
        return 'moins_1_an'
    elif 1 <= years <= 2:
        return 'entre_1_2_ans'
    elif 2 < years <= 5:
        return 'entre_2_5_ans'
    elif 5 < years <= 10:
        return 'entre_5_10_ans'
    else:
        return 'plus_10_ans'

def map_education(edu):
    edu = str(edu).lower()
    if "bachelor" in edu or "licence" in edu:
        return 'licence'
    elif "master" in edu or "mba" in edu:
        return 'master'
    elif "engineer" in edu or "ingénieur" in edu:
        return 'ingénierie'
    elif "phd" in edu or "doctor" in edu:
        return 'doctorat'
    else:
        return None

class Command(BaseCommand):
    help = 'Importer un CSV et mapper vers User, Candidat, OffreEmploi, Candidature'

    def handle(self, *args, **kwargs):
        print("📂 BASE_DIR :", settings.BASE_DIR)
        dataset_dir = os.path.join(settings.BASE_DIR, 'dataset')

        print("📁 Contenu du dossier dataset :")
        print(os.listdir(dataset_dir))  # <-- Liste les fichiers dans le dossier pour vérifier

        file_path = os.path.join(dataset_dir, 'AI_Resume_Screening.csv')
        print("📄 Chemin du fichier :", file_path)
        print("📌 Fichier existe :", os.path.exists(file_path))

        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            print("✅ Données chargées avec succès !")
            print(df.head())  # Affiche les premières lignes pour vérification
        else:
            print("❌ Le fichier n'existe pas à l'emplacement donné.")


        for index, row in df.iterrows():
            username = row['Name'].replace(" ", "").lower()

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'role': 'candidat'}
            )

            candidat, _ = Candidat.objects.get_or_create(
                user=user,
                defaults={
                    'niveau_experience': map_experience(float(row['Experience (Years)'])),
                    'niveau_etude': map_education(row['Education']),
                }
            )

            offre, _ = OffreEmploi.objects.get_or_create(
                titre=row['Job Role'],
                defaults={
                    'competences': row['Skills'],
                    'recruteur': User.objects.filter(role='recruteur').first(),  # ou spécifie un recruteur par défaut
                }
            )

            label = 1 if str(row['Recruiter Decision']).strip().lower() == 'hire' else 0

            Candidature.objects.get_or_create(
                candidat=candidat,
                offre=offre,
                defaults={
                    'label': label,
                    'statut': 'EN_ATTENTE',
                    'date_postulation': timezone.now().date()
                }
            )
            print(f"➡️ CV {index + 1}")
            print(f"👤 Nom: {row['Name']} ➜ User.username: {user.username}")
            print(f"📊 Expérience: {row['Experience (Years)']} ➜ {candidat.niveau_experience}")
            print(f"🎓 Éducation: {row['Education']} ➜ {candidat.niveau_etude}")
            print(f"💼 Job Role: {row['Job Role']} ➜ {offre.titre}")
            print(f"🧠 Compétences: {row['Skills']} ➜ {offre.competences}")
            print(f"✅ Décision: {row['Recruiter Decision']} ➜ Label: {label}")
            print("-" * 60)

        print("✅ Import terminé avec succès.")
