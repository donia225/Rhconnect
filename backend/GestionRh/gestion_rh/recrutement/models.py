from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('candidat', 'Candidat'),
        ('gestionnaire_rh', 'Gestionnaire RH'),
        ('recruteur', 'Recruteur'),
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

# Modèle Formation
class Formation(models.Model):
    TYPE_CHOICES = [
        ('En ligne', 'En ligne'),
        ('Présentiel', 'Présentiel'),
        ('Hybride', 'Hybride'),
    ]
    titre = models.CharField(max_length=255)
    description = models.TextField()
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    duree = models.IntegerField()
    type_formation = models.CharField(max_length=50, choices=TYPE_CHOICES)
    cout = models.FloatField(blank=True, null=True)
    certification = models.BooleanField(default=False)

    def __str__(self):
        return self.titre

# Modèle Participation à une Formation
class ParticipationFormation(models.Model):
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="formations")
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="participants")

    def __str__(self):
        return f"{self.candidat.user.username} participe à {self.formation.titre}"

class Candidature(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REJETEE', 'Rejetée'),
    ]
    
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="candidatures")
    offre = models.ForeignKey(OffreEmploi, on_delete=models.CASCADE, related_name="candidatures")
    date_postulation = models.DateField(auto_now_add=True)
    score_matching = models.FloatField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    
    # Nouveau champ : Vérifie si l'IA a analysé la candidature
    analyse_effectuee = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.candidat.user.username} - {self.offre.titre}"


class IAModule(models.Model):
    candidature = models.OneToOneField(
        Candidature, on_delete=models.CASCADE, related_name="analyse_ia"
    )
    score_matching = models.FloatField(blank=True, null=True)
    recommandations = models.TextField(blank=True, null=True)

    def analyser_cv(self):
        # Simulation de l'analyse IA (à remplacer par un vrai modèle IA)
        self.score_matching = 85.7  # Exemple : score fictif
        self.recommandations = "Ce candidat correspond bien au poste."
        self.save()

        # Mise à jour du statut dans Candidature
        self.candidature.analyse_effectuee = True
        self.candidature.save()

    def __str__(self):
        return f"Analyse IA pour {self.candidature}"

