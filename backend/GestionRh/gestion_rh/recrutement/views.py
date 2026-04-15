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
from django.db import transaction
import unicodedata




User = get_user_model()

def _normalize(s: str) -> str:
    """
    Normalise une chaîne pour comparaison tolérante :
    - enlève accents/diacritiques
    - passe en minuscules
    - supprime tout sauf [a-z0-9]
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s



@api_view(['POST'])
def register_user(request):
    data = request.data

    required_fields = ['email', 'password', 'nom', 'prenom']
    for field in required_fields:
        if field not in data or not data[field]:
            return Response({'message': f'Le champ "{field}" est requis.'}, status=status.HTTP_400_BAD_REQUEST)

    email = data['email']
    password = data['password']
    nom = data['nom']
    prenom = data['prenom']

    if User.objects.filter(username=email).exists():
        return Response({'message': 'Cet email est déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=email,
        last_name=nom,
        first_name=prenom,
        email=email,
        password=password,
        role='candidat'  
    )

    candidat = Candidat.objects.create(
        user=user,
        numero_tel=data.get('numero_tel', ''),  
        adresse=data.get('adresse', ''),  
        cv=data.get('cv', None)  
    )


    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        'message': 'Inscription réussie !',
        'token': access_token,
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'nom': user.last_name,
            'prenom': user.first_name,
            'email': user.email,
            'role': user.role,  
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
        user = User.objects.get(email=email)  
    except User.DoesNotExist:
        return Response({'message': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

  
    user = authenticate(username=user.username, password=password)

    if user is not None:
    
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'message': 'Connexion réussie !',
            'token': access_token,
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'nom': user.last_name,
                'prenom': user.first_name,
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
            pass 
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
        offres = OffreEmploi.objects.all().order_by('-id')  

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

@api_view(['PUT', 'PATCH'])
def modifier_offre(request, id):
    try:
        offre = OffreEmploi.objects.get(id=id)
    except OffreEmploi.DoesNotExist:
        return Response({'message': 'Offre introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = OffreEmploiSerializer(
        offre, data=request.data, partial=(request.method == 'PATCH')
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def _build_offer_description(offre) -> str:
    parts = []
    titre = getattr(offre, "titre", "") or ""
    desc  = getattr(offre, "description", "") or ""
    comp  = getattr(offre, "competences", "") or ""


    if titre: parts.append(f"Titre: {titre}")
    if desc:  parts.append(f"Description: {desc}")
    if comp:  parts.append(f"Compétences: {comp}")
  

    out = "\n".join(parts).strip()
    return out or "Offre sans détails fournis."

# """ @api_view(['POST'])
# @parser_classes([MultiPartParser])
# @permission_classes([AllowAny])
# from ml_models.ai_rag import evaluate_candidate, extract_text_any
# def upload_cv(request):
#     tmp_path = None

#     try:
#         fichier_cv  = request.FILES.get('cv')
#         candidat_id = request.data.get('candidat')
#         offre_id    = request.data.get('offre')

#         if not fichier_cv or not candidat_id or not offre_id:
#             return Response({"error": "Champs requis manquants (cv, candidat, offre)."}, status=400)

#         candidat = get_object_or_404(Candidat, id=candidat_id)
#         offre    = get_object_or_404(OffreEmploi, id=offre_id)

#         # --- Vérification du format PDF ---
#         name = getattr(fichier_cv, "name", "") or "cv.pdf"
#         base, ext = os.path.splitext(name)
#         if ext.lower() != ".pdf":
#             return Response({"error": "Le CV doit être en PDF seulement."}, status=400)

#         # --- Sauvegarde temporaire du fichier ---
#         with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
#             for chunk in fichier_cv.chunks():
#                 tmp.write(chunk)
#             tmp_path = tmp.name

#         # --- Vérification de cohérence Nom/Prénom ---
#         u = getattr(candidat, "user", None)
#         prenom_cand = (getattr(candidat, "prenom", "") or (u.first_name if u else "")).strip()
#         nom_cand    = (getattr(candidat, "nom", "")    or (u.last_name  if u else "")).strip()

#         n_first = _normalize(prenom_cand)
#         n_last  = _normalize(nom_cand)
#         if not n_first or not n_last:
#             return Response({"error": "Nom et/ou prénom du candidat introuvables pour la vérification."}, status=400)

#         n_file = _normalize(base)
#         filename_match = (n_first in n_file) and (n_last in n_file)

#         content_match = False
#         if not filename_match:
#             try:
#                 pdf_text = extract_text_any(tmp_path)
#             except Exception as e:
#                 print(f"[PDF][WARN] extract_text_any failed: {type(e).__name__}: {e}")
#                 pdf_text = ""
#             n_text = _normalize(pdf_text)
#             if n_text:
#                 content_match = ((n_first in n_text and n_last in n_text))

#         if not (filename_match or content_match):
#             return Response({
#                 "error": (
#                     "Le nom/prénom dans le CV ne correspond pas au candidat. "
#                     "Vérifie que le PDF contient le nom complet et/ou renomme le fichier "
#                     "ex: Prenom_Nom_CV.pdf"
#                 )
#             }, status=400)

#         # --- Création de la candidature ---
#         with transaction.atomic():
#             if hasattr(candidat, "cv"):
#                 candidat.cv = fichier_cv
#             candidat.save()

#             candidature = Candidature.objects.create(
#                 candidat=candidat,
#                 offre=offre,
#                 statut='EN_ATTENTE',
#                 label='',
#                 ai_score=None,
#                 ai_notes="",
#                 ai_strengths=[],
#                 ai_missing=[],
#                 ai_evidence=[],
#             )

#         ai_status = "SKIPPED"
#         decision  = ""
#         scores    = {}
#         exp_years = 0.0

#         # --- Évaluation IA ---
#         try:
#             offer_text = _build_offer_description(offre)
#             rag_res = evaluate_candidate(offer_text, tmp_path)

#             if not isinstance(rag_res, dict):
#                 raise ValueError("Unexpected AI output type")
#             if "error" in rag_res:
#                 raise RuntimeError(rag_res["error"])

#             decision   = str(rag_res.get("decision", "")).strip()
#             scores     = rag_res.get("match_scores", {}) or {}

#             overall = int(scores.get("overall", 0) or 0)
#             exp_years = float(rag_res.get("exp_years", 0.0) or 0.0)

#             missing = rag_res.get("missing_requirements", []) or []
#             if not isinstance(missing, list):
#                 missing = [str(missing)]

#             evidence = rag_res.get("evidence", {}) or {}
#             if not isinstance(evidence, dict):
#                 evidence = {}

#             strengths = (
#                 rag_res.get("strengths")
#                 or rag_res.get("matched_skills")
#                 or evidence.get("skills")
#                 or []
#             )
#             if not isinstance(strengths, list):
#                 strengths = [str(strengths)]

#             evidence_list = []
#             for key in ("skills", "education", "experience"):
#                 items = evidence.get(key) or []
#                 if isinstance(items, list):
#                     for v in items[:6]:
#                         evidence_list.append(f"{key}: {v}")
#                 elif items:
#                     evidence_list.append(f"{key}: {items}")

#             notes = str(rag_res.get("notes", "") or "")

#             # --- Mise à jour IA dans la DB ---
#             with transaction.atomic():
#                 candidature.label        = decision
#                 candidature.ai_score     = overall
#                 candidature.ai_notes     = notes
#                 candidature.ai_strengths = strengths
#                 candidature.ai_missing   = missing
#                 candidature.ai_evidence  = evidence_list
#                 candidature.save()

#             ai_status = "OK"

#             # =======================================================
#             # 🚀 Nouvelle logique : une seule candidature EN_ATTENTE
#             # =======================================================
#             try:
#                 toutes = Candidature.objects.filter(candidat=candidat)
#                 hires = toutes.filter(label__iexact='Hire').order_by('-ai_score')

#                 en_attente = toutes.filter(statut='EN_ATTENTE')

#                 if hires.exists():
#                     meilleure = hires.first()
#                     # ✅ la meilleure reste en attente pour validation du recruteur
#                     if meilleure.statut == 'EN_ATTENTE':
#                         meilleure.statut = 'EN_ATTENTE'
#                         meilleure.save(update_fields=['statut'])

#                     # ❌ les autres candidatures "Hire" → REJETÉES
#                     hires.exclude(id=meilleure.id).filter(statut='EN_ATTENTE').update(statut='REJETEE')

#                     # ❌ les autres non "Hire" → également REJETÉES
#                     toutes.exclude(id__in=hires.values_list('id', flat=True)).filter(statut='EN_ATTENTE').update(statut='REJETEE')
#                 else:
#                     # S’il n’y a aucune "Hire" → toutes restent en attente
#                     pass

#             except Exception as e:
#                 print(f"[AUTO-SELECTION][WARN] {type(e).__name__}: {e}")

#         except Exception as ia_err:
#             ai_status = "FAILED"
#             print(f"[AI][ERROR] {type(ia_err).__name__}: {ia_err}")

#         # --- Réponse finale ---
#         data = CandidatureSerializer(candidature, context={'request': request}).data
#         data.update({
#             "message": "CV déposé avec succès",
#             "ai_status": ai_status,
#             "rag_decision": decision,
#             "rag_scores": scores,
#             "exp_years": exp_years,
#             "dejapostule": True
#         })
#         return Response(data, status=201)

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)

#     finally:
#         if tmp_path:
#             try:
#                 os.remove(tmp_path)
#             except Exception:
#                 pass """




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
            'cv': candidat.cv.url if candidat.cv else None
        }
        return Response(data)

    elif request.method == 'PUT':

        user.first_name = request.data.get('prenom', user.first_name)
        user.last_name = request.data.get('nom', user.last_name)
        user.save()


        candidat.date_naissance = request.data.get('date_naissance')
        candidat.niveau_etude = request.data.get('niveau_etude')
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
        u = c.candidat.user
        full_name = (u.get_full_name().strip()
                     or u.username)
        cv_url = request.build_absolute_uri(c.candidat.cv.url) if c.candidat.cv else None
        result.append({
            'id': c.id,
            'candidat': full_name,
            'offre': c.offre.titre,
            'statut': c.statut,
            'cv_link': cv_url,
            'label': c.label,                       
            'label_text': LABEL_TEXT.get(c.label),
            'ai_score': getattr(c, 'ai_score', None),
             'ai_notes': getattr(c, 'ai_notes', '') or '',
            'ai_strengths': getattr(c, 'ai_strengths', []) or [],
            'ai_missing': getattr(c, 'ai_missing', []) or [],
            'ai_evidence': getattr(c, 'ai_evidence', []) or [],
            
        })
    return Response(result, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidatures_gestionnaire_rh(request):
    candidatures = Candidature.objects.all()

    result = []
    for c in candidatures:
        u = c.candidat.user
        full_name = (u.get_full_name().strip()
                     or u.username)
        cv_url = request.build_absolute_uri(c.candidat.cv.url) if c.candidat.cv else None
        result.append({
            'id': c.id,
            'candidat': full_name,
            'offre': c.offre.titre,
            'statut': c.statut,
            'cv_link': cv_url,
            'label': c.label,
            'ai_score': c.ai_score,

            
      
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
@permission_classes([permissions.IsAuthenticated])
def get_suivis_employe(request, employe_id):
    """
    Retourne le profil + tous les suivis (avec objectifs/notes/commentaires).
    """
    employe = get_object_or_404(Employe, id=employe_id)
    suivis = SuiviCarriereEmploye.objects.filter(employe=employe).order_by('date_changement')
    payload = {'employe': employe, 'suivi_carriere': suivis}
    serializer = EmployeProfilEtSuivisSerializer(payload)
    return Response(serializer.data, status=200)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ajouter_suivi_carriere(request):
    """
    Crée un suivi avec objectifs + notes (0..10) + commentaires.
    """
    serializer = SuiviCarriereEmployeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employe_profil_et_suivi(request):
   
    user = request.user

    if user.role != 'employe':
        return Response({'error': 'Non autorisé'}, status=403)

    try:
        employe = Employe.objects.get(user=user)
    except Employe.DoesNotExist:
        return Response({'error': 'Employé introuvable'}, status=404)
    
    cand = getattr(user, 'candidat_profile', None)

    def abs_url(f):
        try:
            return request.build_absolute_uri(f.url) if f and hasattr(f, 'url') else None
        except Exception:
            return None

    profil = {
        'id': employe.id,
        'prenom': user.first_name,
        'nom': user.last_name,
        'email': user.email,
        'avatar': abs_url(user.avatar),           
        'numero_tel': getattr(cand, 'numero_tel', None),
        'adresse': getattr(cand, 'adresse', None),
        'date_naissance': getattr(cand, 'date_naissance', None),

        'poste_actuel': employe.poste_actuel,
        'departement': employe.departement,
        'date_embauche': employe.date_embauche,
    }   

    suivis = employe.suivis.all().order_by('-date_changement').values(
        'ancien_poste', 'nouveau_poste', 'date_changement', 'est_promotion' , 'commentaire', 'notes', 'objectifs_plan'
    )
         

    return Response({
        'profil': profil,
        'suivi_carriere': list(suivis)
    })

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_employe_profile(request):
    user = request.user
    if user.role != 'employe':
        return Response({'error': 'Non autorisé'}, status=403)

    payload = request.data or {}
  
    for k in ('first_name', 'last_name', 'email'):
        if k in payload:
            setattr(user, k, payload[k])

    user.save()


    cand, _ = Candidat.objects.get_or_create(user=user)
    for k in ('numero_tel', 'adresse', 'date_naissance'):
        if k in payload:
            setattr(cand, k, payload[k])
    cand.save()

    return Response({'message': 'Profil mis à jour.'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    user = request.user
    if 'avatar' not in request.FILES:
        return Response({'error': 'Fichier avatar manquant.'}, status=400)

    user.avatar = request.FILES['avatar']
    user.save()
    return Response({'avatar': request.build_absolute_uri(user.avatar.url)}, status=200)


