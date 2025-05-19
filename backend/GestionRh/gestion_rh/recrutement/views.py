from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from .models import OffreEmploi, Candidature
from .serializers import CandidatureSerializer, OffreEmploiSerializer
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Candidat
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from .ia_tests.analyse_cv import analyser_cv
from PyPDF2 import PdfReader, PdfWriter


User = get_user_model()  # Pour s'assurer qu'on utilise bien le modèle User personnalisé

@api_view(['POST'])
def register_user(request):
    data = request.data

    # Vérifier que tous les champs nécessaires sont fournis
    required_fields = ['email', 'password', 'nom', 'prenom']
    for field in required_fields:
        if field not in data or not data[field]:
            return Response({'message': f'Le champ "{field}" est requis.'}, status=status.HTTP_400_BAD_REQUEST)

    email = data['email']
    password = data['password']
    nom = data['nom']
    prenom = data['prenom']

    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username=email).exists():
        return Response({'message': 'Cet email est déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ **Créer un nouvel utilisateur avec le rôle "candidat"**
    user = User.objects.create_user(
        username=email,
        first_name=nom,
        last_name=prenom,
        email=email,
        password=password,
        role='candidat'  # Le rôle est forcé à "candidat"
    )

    # ✅ **Créer un profil Candidat lié à cet utilisateur**
    candidat = Candidat.objects.create(
        user=user,
        numero_tel=data.get('numero_tel', ''),  # Champ optionnel
        adresse=data.get('adresse', ''),  # Champ optionnel
        cv=data.get('cv', None)  # Champ optionnel pour le CV
    )

    # ✅ **Générer un token JWT après l'inscription**
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        'message': 'Inscription réussie !',
        'token': access_token,
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'nom': user.first_name,
            'prenom': user.last_name,
            'email': user.email,
            'role': user.role,  # ✅ Toujours "candidat"
            'candidat_id': candidat.id,
            'numero_tel': candidat.numero_tel,
            'adresse': candidat.adresse,
            'cv': candidat.cv.url if candidat.cv else None
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login_user(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')

    try:
        user = User.objects.get(email=email)  # ✅ Find user by email
    except User.DoesNotExist:
        return Response({'message': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

    # ✅ Authenticate using the actual username
    user = authenticate(username=user.username, password=password)

    if user is not None:
        # ✅ Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'message': 'Connexion réussie !',
            'token': access_token,
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'nom': user.first_name,
                'prenom': user.last_name,
                'email': user.email,
                'role': user.role
            }
        }, status=status.HTTP_200_OK)
    
    return Response({'message': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_offres(request):
    user = request.user
    if user.role == "recruteur":
        offres = OffreEmploi.objects.filter(recruteur=user)
    else:
        offres = OffreEmploi.objects.all().order_by('-id')  # Dernières en premier
    serializer = OffreEmploiSerializer(offres, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def ajouter_offre(request):
    serializer = OffreEmploiSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def supprimer_offre(request, id):
    try:
        offre = OffreEmploi.objects.get(id=id)
    except OffreEmploi.DoesNotExist:
        return Response({'message': "Offre non trouvée."}, status=status.HTTP_404_NOT_FOUND)

    offre.delete()
    return Response({'message': "Offre supprimée avec succès."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT'])
def modifier_offre(request, id):
    try:
        offre = OffreEmploi.objects.get(id=id)
    except OffreEmploi.DoesNotExist:
        return Response({'message': 'Offre introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = OffreEmploiSerializer(offre, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def upload_cv(request):
    try:
        file = request.FILES.get('cv')
        offre_id = request.POST.get('offre')
        candidat_id = request.POST.get('candidat')

        if not file or not offre_id or not candidat_id:
            return Response({"error": "Données manquantes."}, status=400)

        candidat_obj = Candidat.objects.get(pk=candidat_id)
        offre_obj = OffreEmploi.objects.get(pk=offre_id)

        # 1. Enregistrement temporaire du fichier
        from django.core.files.storage import default_storage
        path_temp = default_storage.save(f'temp_cv/{file.name}', file)
        path_complet = default_storage.path(path_temp)
        
         # ✅ 1.b Modifier les métadonnées du PDF (titre affiché)
        reader = PdfReader(path_complet)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        writer.add_metadata({'/Title': file.name})

        with open(path_complet, 'wb') as f:
            writer.write(f)

        # 2. Récupérer les compétences attendues de l’offre
        competences_attendues = []
        if offre_obj.competences:
            competences_attendues = [c.strip().lower() for c in offre_obj.competences.split(',') if c.strip()]

        # 3. Analyse IA
        score = analyser_cv(path_complet, competences_attendues)

        # 4. Création de la candidature avec score
        candidature = Candidature.objects.create(
            candidat=candidat_obj,
            offre=offre_obj,
            statut='EN_ATTENTE',
            analyse_effectuee=True,
            score_matching=score
        )

        # 5. Sauvegarder le CV dans le profil du candidat
        candidat_obj.cv = file
        candidat_obj.save()

        return Response({"message": "CV enregistré et analysé", "score_matching": score})
    
    except Exception as e:
        import traceback
        return Response({"error": str(e), "trace": traceback.format_exc()}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidat_id(request):
    user = request.user

    if user.role != 'candidat':
        return Response({'error': 'Utilisateur non autorisé'}, status=403)

    try:
        candidat = Candidat.objects.get(user=user)
        return Response({'candidat_id': candidat.id})
    except Candidat.DoesNotExist:
        return Response({'error': 'Candidat introuvable'}, status=404)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def candidat_profil(request):
    user = request.user
    try:
        candidat = Candidat.objects.get(user=user)
    except Candidat.DoesNotExist:
        return Response({'error': 'Profil candidat introuvable'}, status=404)

    if request.method == 'GET':
        data = {
            'nom': user.last_name,
            'prenom': user.first_name,
            'date_naissance': candidat.date_naissance,
            'niveau_etude': candidat.niveau_etude,
            'niveau_experience': candidat.niveau_experience,
            'numero_tel': candidat.numero_tel,
            'adresse': candidat.adresse,
            'cv': candidat.cv.url if candidat.cv else None,
        }
        return Response(data)

    elif request.method == 'PUT':
        # Maj données utilisateur (si autorisé)
        user.first_name = request.data.get('prenom', user.first_name)
        user.last_name = request.data.get('nom', user.last_name)
        user.save()

        # Maj données candidat
        candidat.date_naissance = request.data.get('date_naissance')
        candidat.niveau_etude = request.data.get('niveau_etude')
        candidat.niveau_experience = request.data.get('niveau_experience')
        candidat.numero_tel = request.data.get('numero_tel')
        candidat.adresse = request.data.get('adresse')

        # Upload fichier CV si envoyé
        if 'cv' in request.FILES:
            candidat.cv = request.FILES['cv']

        candidat.save()

        return Response({'message': 'Profil mis à jour'})

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_candidatures(request):
    user = request.user
    # Filtrer les candidatures du candidat connecté
    candidatures = Candidature.objects.filter(candidat__user=user).select_related('offre')
    data = [
        {
            'offre_titre': c.offre.titre,
            'statut': c.statut,
            'date_postulation': c.date_postulation,
        }
        for c in candidatures
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidatures_recruteur(request):
    user = request.user
    candidatures = Candidature.objects.filter(offre__recruteur=user).order_by('-score_matching')  # trie par score
    result = []
    for c in candidatures:
        cv_url = request.build_absolute_uri(c.candidat.cv.url) if hasattr(c.candidat, 'cv') and c.candidat.cv else None
        result.append({
            'id': c.id,
            'candidat': c.candidat.user.last_name,
            'offre': c.offre.titre,
            'score': c.score_matching if c.score_matching is not None else 0,
            'analyse_effectuee': c.analyse_effectuee,
            'statut': c.statut,
            'cv_link': cv_url,
            'tag_ia': "Matching IA détecté" if c.analyse_effectuee else "Analyse manuelle requise"
        })
    return Response(result)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_statut_candidature(request, id):
    try:
        candidature = Candidature.objects.get(id=id, offre__recruteur=request.user)
    except Candidature.DoesNotExist:
        return Response({'error': 'Candidature introuvable'}, status=404)

    statut = request.data.get('statut')
    if statut not in ['EN_ATTENTE', 'ACCEPTEE', 'REJETEE']:
        return Response({'error': 'Statut invalide'}, status=400)

    candidature.statut = statut
    candidature.save()
    return Response({'success': 'Statut mis à jour'})