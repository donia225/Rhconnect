import os
import sys
import django
import pandas as pd

# ➕ Ajouter le chemin racine du projet au PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(BASE_DIR)

# 🔧 Spécifier le bon module de configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionRh.gestion_rh.settings')


# ✅ Initialiser Django
django.setup()

# 📦 Importer les modèles après configuration Django
from recrutement.models import Candidature

# 🟩 Construction des données
data = []
for c in Candidature.objects.select_related('candidat').all():
    data.append({
        'niveau_etude': c.candidat.niveau_etude,
        'niveau_experience': c.candidat.niveau_experience,
        'score_matching': c.score_matching,
        'statut': c.statut,
    })

# 📤 Export CSV
df = pd.DataFrame(data)
df.to_csv('tes_donnees.csv', index=False)
print("✅ Fichier CSV généré : tes_donnees.csv")
