from django.urls import include, path

from .views import ajouter_offre, candidat_profil, confirmer_embauche, get_candidat_id, get_candidatures_gestionnaireRH, liste_offres, login_user, mes_candidatures, modifier_offre, register_user, request_password_reset, reset_password, supprimer_offre, update_statut_candidature, upload_cv, get_candidatures_recruteur
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import EmployeViewSet, SuiviCarriereEmployeViewSet

router = DefaultRouter()
router.register(r'employes', EmployeViewSet)
router.register(r'suivis', SuiviCarriereEmployeViewSet)

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),

    path('request-password-reset/', request_password_reset),
    path('reset-password/<uidb64>/<token>/', reset_password),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/social/', include('allauth.socialaccount.urls')),
    path('offres/', liste_offres, name='liste_offres'),
    path('ajouter/', ajouter_offre, name='ajouter_offre'),
    path('offres/<int:id>/', supprimer_offre, name='supprimer_offre'),
    path('offres/modifier/<int:id>/', modifier_offre, name='modifier_offre'),
    path('upload-cv/', upload_cv, name='upload_cv'),
    path('get-candidat-id/', get_candidat_id, name='get_candidat_id'),
    path('mes-candidatures/', mes_candidatures, name='mes_candidatures'),
    path('profil-candidat/', candidat_profil, name='candidat_profil'),
    path('candidatures-recruteur', get_candidatures_recruteur, name='get_candidatures_recruteur'),
    path('candidature/<int:id>/update-statut', update_statut_candidature, name='update-statut-candidature'),
    path('confirmer-embauche/<int:candidature_id>/', confirmer_embauche),
    path('candidatures-gestionnaire/', get_candidatures_gestionnaireRH, name='get_candidatures'),


    path('', include(router.urls)),
] 

