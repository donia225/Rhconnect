# recrutement/serializers.py

from rest_framework import serializers
from .models import Candidature, OffreEmploi

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

