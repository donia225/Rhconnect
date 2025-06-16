# recrutement/serializers.py

from rest_framework import serializers
from .models import Candidature, OffreEmploi, Employe, SuiviCarriereEmploye
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'role', 'email']

class OffreEmploiSerializer(serializers.ModelSerializer):
    nb_candidatures = serializers.SerializerMethodField()
    class Meta:
        model = OffreEmploi
        fields = '__all__'  # ou liste personnalisée
    def get_nb_candidatures(self, obj):
        return obj.candidatures.count()
    
class CandidatureSerializer(serializers.ModelSerializer):
    candidat_nom = serializers.CharField(source="candidat.user.first_name", read_only=True)
    offre_titre = serializers.CharField(source="offre.titre", read_only=True)

    class Meta:
        model = Candidature
        fields = ['id', 'candidat_nom', 'offre_titre', 'statut']

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

