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
    @property
    def full_name(self):
        return (f"{self.first_name} {self.last_name}").strip() or self.username

   

    def __str__(self):
        return f"{self.username} - {self.role}"

# Modèle Candidat
class Candidat(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidat_profile')
    numero_tel = models.CharField(max_length=8, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='uploads/cv/', blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
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

class NiveauEtude(models.TextChoices):
    BAC        = 'bac',        'Baccalauréat'
    BAC_2      = 'bac+2',      'Bac+2 (BTS/DUT/ISET)'
    LICENCE    = 'licence',    'Licence (Bac+3)'
    MASTER     = 'master',     'Master / Mastère (Bac+5)'
    INGENIEUR  = 'ingenieur',  "Diplôme d'ingénieur (Bac+5)"
    MBA        = 'mba',        'MBA / Mastère spécialisé'
    DOCTORAT   = 'doctorat',   'Doctorat'
class OffreEmploi(models.Model):
    titre = models.CharField(max_length=100)
    description = models.TextField()
    salaire = models.FloatField()
    competences = models.TextField(blank=True, null=True)
    type_poste = models.CharField(max_length=20, blank=True, null=True)
    EXPERIENCE_CHOICES = [
        ('aucune', 'Aucune'),
        ('moins_1_an', "Moins de 1 an"),
        ('entre_1_2_ans', "1 à 2 ans"),
        ('entre_2_5_ans', "2 à 5 ans"),
        ('entre_5_10_ans', "5 à 10 ans"),
        ('plus_10_ans', "Plus de 10 ans"),
    ]
    experience = models.CharField(max_length=50, choices=EXPERIENCE_CHOICES, blank=True, null=True)
    niveau_etude = models.JSONField(default=list, blank=True)
    DISPONIBILITE_CHOICES = [
        ('plein_temps', 'Plein temps'),
        ('mi_temps', 'Mi-temps'),
        ('temps_partiel_weekend', 'Temps partiel (week-end)'),
        ('temps_partiel_soir', 'Temps partiel (soir)'),
        ('horaires_flexibles', 'Horaires flexibles'),
        ('travail_en_shifts', 'Travail en shifts (2x8/3x8)'),
        ('saisonnier', 'Saisonnier'),
    ]
    disponibilite = models.CharField(
        max_length=100, choices=DISPONIBILITE_CHOICES, blank=True, null=True
    )
    MODALITE_CHOICES = [
        ('sur_site', 'Sur site'),
        ('hybride', 'Hybride'),
        ('teletravail', 'Télétravail'),
    ]
    modalite = models.CharField(
        max_length=20,
        choices=MODALITE_CHOICES,
        blank=True, null=True
    )
    langues = models.TextField(blank=True, null=True)
    date_publication = models.DateField(auto_now_add=True, blank=True)
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
    label = models.CharField(max_length=16, choices=[("Hire","Hire"), ("Reject","Reject")], null=True, blank=True)
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
    objectifs = models.JSONField(default=list, blank=True)
    notes = models.JSONField(default=dict, blank=True) 

    def __str__(self):
        return f"{self.employe.user.username} -> {self.nouveau_poste}"






