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

    def __str__(self):
        return f"Candidat: {self.user.username}"


class OffreEmploi(models.Model):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    salaire = models.FloatField()
    competences = models.TextField(blank=True, null=True)
    # ✅ Référence au modèle `User` défini ci-dessus
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

