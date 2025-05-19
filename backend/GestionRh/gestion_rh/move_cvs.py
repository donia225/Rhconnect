import os
import shutil
from django.conf import settings
import django

# Initialiser Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_rh.settings")
django.setup()

from recrutement.models import Candidat  # adapte si le modèle est ailleurs

# Ancien répertoire (où sont les fichiers actuels)
old_dir = os.path.join(settings.BASE_DIR, 'gestion_rh', 'uploads', 'cv')

# Nouveau répertoire (media/uploads/cv/)
new_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'cv')

# Créer le répertoire cible s’il n’existe pas
os.makedirs(new_dir, exist_ok=True)

# Boucle sur les candidats
for candidat in Candidat.objects.all():
    if candidat.cv:
        old_path = os.path.join(settings.BASE_DIR, 'gestion_rh', candidat.cv.name)
        filename = os.path.basename(candidat.cv.name)
        new_path = os.path.join(new_dir, filename)

        if os.path.exists(old_path):
            print(f"Déplacement de {filename} ...")
            shutil.move(old_path, new_path)

            # Mettre à jour le chemin dans la base de données
            candidat.cv.name = f'uploads/cv/{filename}'
            candidat.save()
        else:
            print(f"⚠️ Fichier non trouvé : {old_path}")
