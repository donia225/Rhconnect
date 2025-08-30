import json
import os, tempfile
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate

from gestion_rh import settings
import re
from .models import Employe, OffreEmploi, Candidature, SuiviCarriereEmploye
from .serializers import CandidatSerializer, CandidatureSerializer, EmployeProfilEtSuivisSerializer, EmployeSerializer, OffreEmploiSerializer, SuiviCarriereEmployeSerializer
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Candidat
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from PyPDF2 import PdfReader, PdfWriter
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.views import APIView


def years_to_level(years: int) -> str:
    y = int(years or 0)
    if y <= 0:  return 'aucune'
    if y < 1:   return 'moins_1_an'
    if y < 2:   return 'entre_1_2_ans'
    if y < 5:   return 'entre_2_5_ans'
    if y < 10:  return 'entre_5_10_ans'
    return 'plus_10_ans'


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

@csrf_exempt
def request_password_reset(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"http://localhost:4200/auth/reset-password/{uid}/{token}"
            send_mail(
                'Réinitialisez votre mot de passe',
                f'Bonjour,\n\nCliquez ici pour changer votre mot de passe : {reset_url}',
                'noreply@votresite.com',
                [email],
                fail_silently=False
            )
        except User.DoesNotExist:
            pass  # Pour des raisons de sécurité, on ne signale pas si l'utilisateur n'existe pas
        return JsonResponse({'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'})

@csrf_exempt
def reset_password(request, uidb64, token):
    if request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            return JsonResponse({'error': 'Les mots de passe ne correspondent pas.'}, status=400)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.set_password(password)
                user.save()
                return JsonResponse({'message': 'Mot de passe mis à jour avec succès.'})
            else:
                return JsonResponse({'error': 'Lien invalide ou expiré.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def liste_offres(request):
    user = request.user if request.user.is_authenticated else None

    if user and hasattr(user, 'role') and user.role == "recruteur":
        offres = OffreEmploi.objects.filter(recruteur=user)
    else:
        offres = OffreEmploi.objects.all().order_by('-id')  # tout public

    serializer = OffreEmploiSerializer(offres, many=True)
    return Response(serializer.data)
class OffresDuRecruteurAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        offres = OffreEmploi.objects.filter(recruteur=user) 
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
@permission_classes([AllowAny])  # mets IsAuthenticated si tu veux sécuriser
def upload_cv(request):
    if not getattr(settings, "ML_ENABLED", False):
        return Response({"error": "ML is disabled on this build."}, status=503)
    from ml_models import predict_cv as pcv
    tmp_path = None
    try:
        fichier_cv = request.FILES.get('cv')
        candidat_id = request.data.get('candidat')
        offre_id = request.data.get('offre')
        projects_count_in = request.data.get('projects_count')  # optionnel

        if not fichier_cv or not candidat_id or not offre_id:
            return Response({"error": "Champs requis manquants (cv, candidat, offre)."}, status=400)

        candidat = get_object_or_404(Candidat, id=candidat_id)
        offre = get_object_or_404(OffreEmploi, id=offre_id)

        # --- 1) Vérif extension + write temp
        name = getattr(fichier_cv, "name", "") or "cv.pdf"
        _, ext = os.path.splitext(name)
        ext = ext.lower()
        if ext not in {".pdf", ".docx", ".doc"}:
            return Response({"error": "Formats acceptés : .pdf, .docx, .doc"}, status=400)

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            for chunk in fichier_cv.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        # --- 2) projects_count (priorité au front, sinon candidat)
        try:
            projects_count = int(projects_count_in) if projects_count_in is not None \
                             else int(getattr(candidat, "projects_count", 0) or 0)
        except Exception:
            projects_count = 0

        # --- 3) PRÉDICTION offer-aware
        pred = pcv.predict_from_pdf_with_offer(
            tmp_path,
            offre_obj=offre,         # _build_offer_description(offre) utilisé en interne
            offer_description=None,  # None => utilise l'objet offre
            projects_count=projects_count,
            debug_topn=15,         # affiche/retourne les 15 meilleurs
            debug_print=True  
        )

        print("=== AI PREDICTION ===")
        print(f"Label: {pred.get('label_text')} ({pred.get('label')}) | Proba: {float(pred.get('proba') or 0):.3f}")

        offer_txt = (pred.get('offer_description_used') or '')
        print("---- OFFER DESCRIPTION ----")
        print(offer_txt[:1000])

        skills_list = pred.get('extracted_skills') or []
        print("---- CV SKILLS ----")
        print(", ".join(skills_list[:40]))
        
        print("---- CV META ----")
        print(f"Experience: {int(pred.get('exp_years') or 0)} ans ({pred.get('exp_phrase') or 'N/A'})")
        print(f"Education: {pred.get('edu_phrase') or 'N/A'}")

        print("---- COSINE SIMS ----")
        print(
        "skills↔desc: %.3f | exp↔desc: %.3f | edu↔desc: %.3f" % (
        float(pred.get('cos_sim_skills_desc') or 0.0),
        float(pred.get('cos_sim_exp_desc') or 0.0),
        float(pred.get('cos_sim_edu_desc') or 0.0),
    )
)
        print("=======================\n")


        #MAJ candidat 
        exp_years = int(pred.get("exp_years") or 0)
        level = years_to_level(exp_years)

        update_fields = []
        if hasattr(candidat, "cv"):
            candidat.cv = fichier_cv
            update_fields.append("cv")
        if hasattr(candidat, "niveau_experience"):
            candidat.niveau_experience = level
            update_fields.append("niveau_experience")
        if hasattr(candidat, "projects_count"):
            if projects_count_in is not None:
                try:
                    candidat.projects_count = int(projects_count_in)
                    update_fields.append("projects_count")
                except Exception:
                    pass
        if update_fields:
            candidat.save(update_fields=update_fields)

        candidature = Candidature.objects.create(
            candidat=candidat,
            offre=offre,
            statut='EN_ATTENTE',
            label=pred.get("label"),
            ai_score=round((pred.get("proba") or 0) * 100, 2),
        )

        data = CandidatureSerializer(candidature, context={'request': request}).data
        data.update({
            "exp_years": exp_years,
            "niveau_experience": level,
            "exp_phrase": pred.get("exp_phrase"),
            "edu_phrase": pred.get("edu_phrase"),
            "cos_sim_skills_desc": pred.get("cos_sim_skills_desc"),
            "cos_sim_exp_desc": pred.get("cos_sim_exp_desc"),
            "cos_sim_edu_desc": pred.get("cos_sim_edu_desc"),
        })
        return Response(data, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deja_postule(request, offre_id):
    user = request.user
    candidat = getattr(user, 'candidat_profile', None)
    if candidat is None:
        return Response({'error': 'Utilisateur non lié à un candidat'}, status=400)

    deja = Candidature.objects.filter(candidat_id=candidat.id, offre_id=offre_id).exists()
    return Response({'dejapostule': deja})

@api_view(['GET'])
@permission_classes([AllowAny])
def list_candidats(request):
    candidats = Candidat.objects.select_related('user').all()
    serializer = CandidatSerializer(candidats, many=True, context={'request': request})
    return Response(serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidat_id(request):
    user = request.user
    if getattr(user, "role", None) != 'candidat':
        return Response({'error': 'Utilisateur non autorisé'}, status=403)

    candidat = get_object_or_404(Candidat.objects.select_related('user'), user=user)

    data = CandidatSerializer(candidat, context={'request': request}).data

    data.update({"candidat_id": candidat.id})

    return Response(data, status=200)

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
            'projects_count': candidat.projects_count
        }
        return Response(data)

    elif request.method == 'PUT':

        user.first_name = request.data.get('prenom', user.first_name)
        user.last_name = request.data.get('nom', user.last_name)
        user.save()


        candidat.date_naissance = request.data.get('date_naissance')
        candidat.niveau_etude = request.data.get('niveau_etude')
        # candidat.niveau_experience = request.data.get('niveau_experience')
        candidat.numero_tel = request.data.get('numero_tel')
        candidat.adresse = request.data.get('adresse')
        candidat.projects_count =request.data.get('projects_count')

        if 'cv' in request.FILES:
            candidat.cv = request.FILES['cv']

        candidat.save()

        return Response({'message': 'Profil mis à jour'})

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_candidatures(request):
    user = request.user
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

LABEL_TEXT = {0: "Reject", 1: "Hire"}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_candidatures_by_candidat(request, id):
    candidat = get_object_or_404(Candidat, id=id)
    candidatures = candidat.candidatures.all()
    serializer = CandidatureSerializer(candidatures, many=True)
    return Response(serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidatures_recruteur(request):
    user = request.user
    qs = (Candidature.objects
          .filter(offre__recruteur=user)
          .select_related('candidat__user', 'offre')
          .order_by('-id'))

    result = []
    for c in qs:
        cv_url = request.build_absolute_uri(c.candidat.cv.url) if c.candidat.cv else None
        result.append({
            'id': c.id,
            'candidat': c.candidat.user.last_name,
            'offre': c.offre.titre,
            'statut': c.statut,
            'cv_link': cv_url,
            'label': c.label,                       
            'label_text': LABEL_TEXT.get(c.label),
            'ai_score': getattr(c, 'ai_score', None)
        })
    return Response(result, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidatures_gestionnaire_rh(request):
    candidatures = Candidature.objects.all()

    result = []
    for c in candidatures:
        cv_url = request.build_absolute_uri(c.candidat.cv.url) if c.candidat.cv else None
        result.append({
            'id': c.id,
            'candidat': c.candidat.user.last_name,
            'offre': c.offre.titre,
            'statut': c.statut,
            'cv_link': cv_url,
            
      
        })

    return Response(result)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_label(request, candidature_id):
    try:

        candidature = Candidature.objects.get(id=candidature_id, offre__recruteur=request.user)

        label = request.data.get("label")
        if label not in [0, 1, "0", "1"]:
            return Response({"error": "Label invalide. Doit être 0 ou 1."}, status=400)

        candidature.label = int(label)
        candidature.save()

        return Response({"success": "Label mis à jour avec succès."})

    except Candidature.DoesNotExist:
        return Response({"error": "Candidature introuvable ou vous n'êtes pas autorisé à la modifier."}, status=404)

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

class EmployeViewSet(viewsets.ModelViewSet):
    queryset = Employe.objects.all()
    serializer_class = EmployeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def suivi(self, request, pk=None):
        employe = self.get_object()
        suivis = employe.suivis.all().order_by('-date_changement')
        serializer = SuiviCarriereEmployeSerializer(suivis, many=True)
        return Response(serializer.data)

class SuiviCarriereEmployeViewSet(viewsets.ModelViewSet):
    queryset = SuiviCarriereEmploye.objects.all()
    serializer_class = SuiviCarriereEmployeSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmer_embauche(request, candidature_id):
    try:
        candidature = Candidature.objects.get(id=candidature_id)
        user = candidature.candidat.user

        Employe.objects.create(
            user=user,
            poste_actuel=candidature.offre.titre,
            date_embauche=timezone.now().date(),
            departement="A définir"
        )
        user.role = 'employe'
        user.save()
        candidature.delete()

        return JsonResponse({'message': f"{user.get_full_name()} est maintenant employé."})
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employe_profil_et_suivi(request):
    """
    ⚙️ Vue pour l'espace Employé :
    Retourne le profil Employé + historique suivi carrière.
    """
    user = request.user

    if user.role != 'employe':
        return Response({'error': 'Non autorisé'}, status=403)

    try:
        employe = Employe.objects.get(user=user)
    except Employe.DoesNotExist:
        return Response({'error': 'Employé introuvable'}, status=404)

    # ✅ Profil de l'employé
    profil = {
        'id': employe.id,
        'nom': user.last_name,
        'prenom': user.first_name,
        'poste_actuel': employe.poste_actuel,
        'date_embauche': employe.date_embauche,
        'departement': employe.departement
    }

    # ✅ Suivi carrière
    suivis = employe.suivis.all().order_by('-date_changement').values(
        'ancien_poste', 'nouveau_poste', 'date_changement', 'est_promotion' , 'commentaire'
    )

    return Response({
        'profil': profil,
        'suivi_carriere': list(suivis)
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suivis_employe(request, employe_id):
    try:
        employe = Employe.objects.get(id=employe_id)
    except Employe.DoesNotExist:
        return Response({'error': 'Employé introuvable'}, status=404)

    suivis = SuiviCarriereEmploye.objects.filter(employe=employe).order_by('-date_changement')

    data = {
        'employe': employe,
        'suivi_carriere': suivis
    }

    serializer = EmployeProfilEtSuivisSerializer(instance=data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ajouter_suivi_carriere(request):
    """
    ➕ Ajouter un élément de suivi de carrière (gestionnaire RH)
    """
    serializer = SuiviCarriereEmployeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def modifier_suivi_carriere(request, suivi_id):
    """
    ✏️ Modifier un élément de suivi de carrière existant
    """
    try:
        suivi = SuiviCarriereEmploye.objects.get(id=suivi_id)
    except SuiviCarriereEmploye.DoesNotExist:
        return Response({'error': 'Suivi introuvable'}, status=404)

    serializer = SuiviCarriereEmployeSerializer(suivi, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)
