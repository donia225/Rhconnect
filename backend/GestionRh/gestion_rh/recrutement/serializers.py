# recrutement/serializers.py

from rest_framework import serializers
from .models import Candidat, Candidature, OffreEmploi, Employe, SuiviCarriereEmploye
from django.contrib.auth import get_user_model

User = get_user_model()

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
    class Meta:
        model = OffreEmploi
        fields = '__all__'  # ou liste personnalisée
    def get_nb_candidatures(self, obj):
        return obj.candidatures.count()
    
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

class SuiviCarriereEmployeSerializer(serializers.ModelSerializer):
    employe = serializers.PrimaryKeyRelatedField(queryset=Employe.objects.all())

    class Meta:
        model = SuiviCarriereEmploye
        fields = ['id', 'employe', 'ancien_poste', 'nouveau_poste', 'date_changement', 'est_promotion', 'commentaire']

class EmployeProfilEtSuivisSerializer(serializers.Serializer):
    employe = EmployeSerializer()
    suivi_carriere = SuiviCarriereEmployeSerializer(many=True)

