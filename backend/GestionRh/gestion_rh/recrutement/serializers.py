# recrutement/serializers.py

from rest_framework import serializers
from .models import Candidat, Candidature, OffreEmploi, Employe, SuiviCarriereEmploye
from django.contrib.auth import get_user_model
from .models import OffreEmploi, NiveauEtude
import re

User = get_user_model()
TITLE_RE = r"^[A-Za-zÀ-ÿ'’`.,()\- ]{3,120}$"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'role', 'email']

class CandidatSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    cv_url = serializers.SerializerMethodField(read_only=True)
    niveau_etude_label = serializers.CharField(source='get_niveau_etude_display', read_only=True)
    niveau_experience = serializers.CharField(read_only=True)
    niveau_experience_label = serializers.CharField(source='get_niveau_experience_display', read_only=True)

    class Meta:
        model = Candidat
        fields = [
            'id',
            'user',
            'numero_tel',
            'adresse',
            'cv',           # nom de fichier
            'cv_url',       # URL absolue
            'date_naissance',
            'projects_count',
            'est_employe',
            'niveau_etude', 'niveau_etude_label',
            'niveau_experience', 'niveau_experience_label',
        ]

    def get_cv_url(self, obj):
        try:
            request = self.context.get('request')
            if obj.cv and hasattr(obj.cv, 'url'):
                # URL absolue si request dispo
                return request.build_absolute_uri(obj.cv.url) if request else obj.cv.url
        except Exception:
            pass
        return None

class OffreEmploiSerializer(serializers.ModelSerializer):
    nb_candidatures = serializers.SerializerMethodField()
    niveau_etude = serializers.ListField(
        child=serializers.ChoiceField(choices=NiveauEtude.values),
        allow_empty=True, required=True
    )
    salaire = serializers.FloatField(min_value=1)
    class Meta:
        model = OffreEmploi
        fields = '__all__'
        read_only_fields = ('id', 'date_publication', 'nb_candidatures')
    def get_nb_candidatures(self, obj):
        return obj.candidatures.count()
    def validate_titre(self, v):
        if not re.fullmatch(TITLE_RE, (v or '').strip()):
            raise serializers.ValidationError(
                "Le titre ne doit contenir que des lettres/espaces/ponctuation simple (pas de chiffres)."
            )
        return v.strip()
    def validate_langues(self, v):
        # "Français, Anglais, Arabe" -> contrôle max 3
        parts = [s.strip() for s in re.split(r'[;,]', v or '') if s.strip()]
        if len(parts) > 3:
            raise serializers.ValidationError("Maximum 3 langues.")
        # on ré-écrit proprement (optionnel)
        return ', '.join(parts)
    def validate_competences(self, value: str):
        items = [s.strip() for s in (value or '').split(',') if s.strip()]
        if not items:
            raise serializers.ValidationError("Au moins une compétence.")
        for tok in items:
            if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", tok):
                raise serializers.ValidationError(f"« {tok} » doit contenir au moins une lettre.")
        # normalise l'espacement
        return ", ".join(items)
    def validate_salaire(self, value):
        if value is None:
            raise serializers.ValidationError("Salaire requis.")
        if value < 300 or value > 20000:
            raise serializers.ValidationError("Salaire mensuel en TND entre 300 et 20 000.")
        return value
    
class CandidatureSerializer(serializers.ModelSerializer):
    candidat = serializers.CharField(source="candidat.user.first_name", read_only=True)
    offre = serializers.CharField(source="offre.titre", read_only=True)
    cv_link = serializers.SerializerMethodField(read_only=True)
    label_text = serializers.CharField(source="get_label_display", read_only=True)  # "Reject"/"Hire"

    class Meta:
        model = Candidature
        fields = ['id', 'candidat', 'offre', 'statut', 'cv_link', 'label', 'label_text', 'ai_score']

    def get_cv_link(self, obj):
        req = self.context.get('request')
        if obj.candidat.cv and hasattr(obj.candidat.cv, 'url'):
            return req.build_absolute_uri(obj.candidat.cv.url) if req else obj.candidat.cv.url
        return None

class EmployeSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Employe
        fields = ['id', 'user', 'poste_actuel', 'date_embauche', 'departement']

ALLOWED_NOTES = {
    'technique','communication','performance','travail_d_equipe','leadership',
    'qualite','respect_delais','autonomie','initiative','orientation_client',
    'assiduite','gestion_stress','securite_conformite','apprentissage','fiabilite'
}
class SuiviCarriereEmployeSerializer(serializers.ModelSerializer):
    objectifs = serializers.ListField(
        child=serializers.CharField(max_length=300),
        required=False, allow_empty=True
    )
    notes = serializers.DictField(
        child=serializers.FloatField(min_value=0, max_value=10),
        required=False
    )

    class Meta:
        model = SuiviCarriereEmploye
        fields = [
            'id','employe','ancien_poste','nouveau_poste','date_changement',
            'est_promotion','commentaire','objectifs','notes'
        ]
    def validate_notes(self, notes):
        unknown = [k for k in notes.keys() if k not in ALLOWED_NOTES]
        if unknown:
            raise serializers.ValidationError(f"Clés non reconnues: {', '.join(unknown)}")
        return notes


class EmployeProfilEtSuivisSerializer(serializers.Serializer):
    employe = EmployeSerializer()
    suivi_carriere = SuiviCarriereEmployeSerializer(many=True)

