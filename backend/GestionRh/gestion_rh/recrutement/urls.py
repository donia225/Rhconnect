from django.urls import include, path

from .views import ajouter_offre, candidat_profil, get_candidat_id, liste_offres, login_user, mes_candidatures, modifier_offre, register_user, supprimer_offre, update_statut_candidature, upload_cv, get_candidatures_recruteur
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('register/', register_user, name='register'),
     path('login/', login_user, name='login'),
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


] 

