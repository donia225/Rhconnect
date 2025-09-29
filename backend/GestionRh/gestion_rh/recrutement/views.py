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
from ml_models.ai_rag import evaluate_candidate



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

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def upload_cv(request):



    tmp_path = None

    try:
        # -------- 1) Entrées --------
        fichier_cv  = request.FILES.get('cv')
        candidat_id = request.data.get('candidat')
        offre_id    = request.data.get('offre')

        if not fichier_cv or not candidat_id or not offre_id:
            return Response({"error": "Champs requis manquants (cv, candidat, offre)."}, status=400)

        candidat = get_object_or_404(Candidat, id=candidat_id)
        offre    = get_object_or_404(OffreEmploi, id=offre_id)

        # Vérifier extension PDF
        name = getattr(fichier_cv, "name", "") or "cv.pdf"
        _, ext = os.path.splitext(name)
        if ext.lower() != ".pdf":
            return Response({"error": "Le CV doit être en PDF seulement."}, status=400)

        # Sauvegarde temporaire du fichier pour extraction
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            for chunk in fichier_cv.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        # -------- 2) Évaluation IA --------
        offer_text = _build_offer_description(offre)
        try:
            rag_res = evaluate_candidate(offer_text, tmp_path)
        except Exception as e:
            return Response({"error": f"AI pipeline failed: {str(e)}"}, status=500)

        if not isinstance(rag_res, dict):
            return Response({"error": "Unexpected AI output type"}, status=502)
        if "error" in rag_res:
            return Response({"error": rag_res["error"]}, status=500)

        decision   = str(rag_res.get("decision", "")).strip()
        scores     = rag_res.get("match_scores", {}) or {}
        overall    = int(scores.get("overall", 0) or 0)
        exp_years  = float(rag_res.get("exp_years", 0.0) or 0.0)

        # Normalisation des champs IA
        missing = rag_res.get("missing_requirements", []) or []
        if not isinstance(missing, list):
            missing = [str(missing)]

        evidence = rag_res.get("evidence", {}) or {}
        if not isinstance(evidence, dict):
            evidence = {}

        strengths = (
            rag_res.get("strengths")
            or rag_res.get("matched_skills")
            or evidence.get("skills")
            or []
        )
        if not isinstance(strengths, list):
            strengths = [str(strengths)]

        # Aplatir evidence -> liste lisible
        evidence_list = []
        for key in ("skills", "education", "experience"):
            items = evidence.get(key) or []
            if isinstance(items, list):
                for v in items[:6]:
                    evidence_list.append(f"{key}: {v}")
            elif items:
                evidence_list.append(f"{key}: {items}")

        notes = str(rag_res.get("notes", "") or "")

                # après parsing rag_res
        print(f"[AI] decision={decision} | overall={overall} | scores={scores}")
        print("missing (top3):", (missing or [])[:3])
        print("evidence sizes:", {k: len((evidence or {}).get(k) or []) for k in ("skills","education","experience")})
        print("notes:", (notes[:200] if notes else "<vide>"))
        

        # -------- 3) Écritures DB atomiques --------
        with transaction.atomic():
            # MAJ candidat
            if hasattr(candidat, "cv"):
                candidat.cv = fichier_cv
            if hasattr(candidat, "niveau_experience"):
                try:
                    candidat.niveau_experience = years_to_level(int(exp_years))
                except Exception:
                    pass
            candidat.save()

            # Création candidature avec champs IA persistés
            candidature = Candidature.objects.create(
                candidat=candidat,
                offre=offre,
                statut='EN_ATTENTE',
                label=decision,
                ai_score=overall,
                ai_notes=notes,
                ai_strengths=strengths,
                ai_missing=missing,
                ai_evidence=evidence_list,
            )
            print(f"[DB] Candidature #{candidature.id} créée pour {candidat} – offre {offre}")
            print(f"[DB] AI score={candidature.ai_score}, decision={candidature.label}")
            print(f"[DB] strengths={len(candidature.ai_strengths or [])}, "
            f"missing={len(candidature.ai_missing or [])}, "
            f"evidence={len(candidature.ai_evidence or [])}, "
            f"notes_len={len(candidature.ai_notes or '')}")

      
   

        # -------- 4) Réponse --------
        data = CandidatureSerializer(candidature, context={'request': request}).data
        # Optionnel: inclure quelques détails bruts IA
        data.update({
            "rag_decision": decision,
            "rag_scores": scores,
            "exp_years": exp_years,
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
            'cv': candidat.cv.url if candidat.cv else None
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
        u = c.candidat.user
        full_name = (u.get_full_name().strip()  # first_name + last_name
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
        full_name = (u.get_full_name().strip()  # first_name + last_name
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
    
#espace Employé : le profil Employé + historique suivi carrière.
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

    # ✅ Profil de l'employé
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

    # ✅ Suivi carrière
    suivis = employe.suivis.all().order_by('-date_changement').values(
        'ancien_poste', 'nouveau_poste', 'date_changement', 'est_promotion' , 'commentaire', 'notes', 'objectifs_plan'
    )
         

    return Response({
        'profil': profil,
        'suivi_carriere': list(suivis)
    })
# modifier profile employe
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


