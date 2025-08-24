from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('candidat', 'Candidat'),
        ('gestionnaire_rh', 'Gestionnaire RH'),
        ('recruteur', 'Recruteur'),
        ('employe', 'Employe')
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidat')

    groups = models.ManyToManyField(Group, related_name="recrutement_users")
    user_permissions = models.ManyToManyField(Permission, related_name="recrutement_users_permissions")

    def __str__(self):
        return f"{self.username} - {self.role}"

# Modèle Candidat
class Candidat(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidat_profile')
    numero_tel = models.CharField(max_length=8, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='uploads/cv/', blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    projects_count = models.PositiveIntegerField(default=0)
    est_employe = models.BooleanField(default=False)
    NIVEAU_ETUDE_CHOICES = [
    ('licence', 'Licence'),
    ('master', 'Master'),
    ('ingénierie', 'Ingénierie'),
    ('doctorat', 'Doctorat'),
    ('expert', 'Expert'),
    ('recherche', 'Chercheur/Recherche'),
    ]
    niveau_etude = models.CharField(max_length=20, choices=NIVEAU_ETUDE_CHOICES, blank=True, null=True)
    NIVEAU_EXPERIENCE_CHOICES = [
    ('aucune', "Aucune expérience"),
    ('moins_1_an', "Moins d'un an"),
    ('entre_1_2_ans', "Entre 1 et 2 ans"),
    ('entre_2_5_ans', "Entre 2 et 5 ans"),
    ('entre_5_10_ans', "Entre 5 et 10 ans"),
    ('plus_10_ans', "Plus que 10 ans"),
]
    niveau_experience = models.CharField(
    max_length=20, choices=NIVEAU_EXPERIENCE_CHOICES, blank=True, null=True
)

    def __str__(self):
        return f"Candidat: {self.user.username}"


class OffreEmploi(models.Model):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    salaire = models.FloatField()
    competences = models.TextField(blank=True, null=True)

    # ✅ Nouveaux champs structurés
    type_poste = models.CharField(max_length=100, blank=True, null=True)  # Ex: CDI, CDD, SIVP
    experience = models.CharField(max_length=100, blank=True, null=True)  # Ex: Moins d’un an
    niveau_etude = models.CharField(max_length=100, blank=True, null=True)  # Ex: Bac, Bac+3
    disponibilite = models.CharField(max_length=100, blank=True, null=True)  # Ex: Plein temps
    langues = models.TextField(blank=True, null=True)  # Ex: Français, Anglais

    # ✅ Publication
    date_publication = models.DateField(auto_now_add=True, blank=True)

    # ✅ Lien avec l'utilisateur recruteur
    recruteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offres")

    def __str__(self):
        return self.titre

class Candidature(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REJETEE', 'Rejetée'),
    ]
    
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="candidatures")
    offre = models.ForeignKey(OffreEmploi, on_delete=models.CASCADE, related_name="candidatures")
    date_postulation = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    label = models.IntegerField(null=True, blank=True, choices=[(0, "Reject"), (1, "Hire")])
    ai_score = models.IntegerField(null=True, blank=True) 


    def __str__(self):
        return f"{self.candidat.user.username} - {self.offre.titre}"
    
class Employe(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employe_profile')
    poste_actuel = models.CharField(max_length=255)
    date_embauche = models.DateField()
    departement = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.poste_actuel}"
    
class SuiviCarriereEmploye(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='suivis')
    ancien_poste = models.CharField(max_length=255, blank=True, null=True)
    nouveau_poste = models.CharField(max_length=255)
    date_changement = models.DateField(auto_now_add=True)
    est_promotion = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employe.user.username} -> {self.nouveau_poste}"






