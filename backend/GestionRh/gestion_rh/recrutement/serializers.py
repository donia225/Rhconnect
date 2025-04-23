# recrutement/serializers.py

from rest_framework import serializers
from .models import OffreEmploi

class OffreEmploiSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffreEmploi
        fields = '__all__'  # ou liste personnalisée
