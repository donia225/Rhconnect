import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({ providedIn: 'root' })
export class EmployeService {
  avatarChanged$ = new BehaviorSubject<string>('');
  private apiUrl = environment.apiUrl;

  // 🔑 Permet aux composants d'écouter le rechargement automatique
  private reloadSubject = new BehaviorSubject<void>(undefined);
  reload$ = this.reloadSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * ✅ Récupère le profil de l'employé connecté + suivi carrière
   */
  getEmployeProfilEtSuivi(): Observable<any> {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    return this.http.get<any>(`${this.apiUrl}/profil-employe/`, { headers });
  }

  /** ✅ Centralise la création des headers */
  private getAuthHeaders() {
    const token = localStorage.getItem('access_token') || '';
    return {
      headers: new HttpHeaders({
        Authorization: `Bearer ${token}`
      })
    };
  }

  /** ✅ Liste des employés */
  getEmployes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/employes/`, this.getAuthHeaders());
  }
    updateEmploye(
    id: number,
    patch: Partial<{ departement: string; poste_actuel: string; date_embauche: string; }>
  ): Observable<any> {
    // ✅ pas de virgule/parenthèse mal placée, URL correcte
    return this.http.patch(
      `${this.apiUrl}/employes/${id}/`,
      patch,
      this.getAuthHeaders()
    );
  }
 getSuivis(employeId: number): Observable<any> {
  const headers = {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  };
  return this.http.get(`${this.apiUrl}/suivis/${employeId}/`, headers);
}



  ajouterSuivi(suivi: any): Observable<any> {
      const headers = {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    };
    return this.http.post(`${this.apiUrl}/ajouter-suivi/`, suivi, headers);
  }

  updateSuivi(id: number, patch: any) {
  return this.http.patch(`${this.apiUrl}/suivi-carriere/${id}/`, patch, this.getAuthHeaders());
}

  // ✏️ Modifier un suivi
  modifierSuivi(id: number, suivi: any): Observable<any> {
     const token = localStorage.getItem('access_token'); // ou 'token' selon ton projet
  const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
  });
    return this.http.put(`${this.apiUrl}/modifier-suivi/${id}/`, {suivi}, { headers });
  }


getMonProfilEtSuivi() {
  // AVANT: return this.http.get(`${this.apiUrl}/employe/profil-et-suivi/`, this.getAuthHeaders());
  return this.http.get(`${this.apiUrl}/profil-employe/`, this.getAuthHeaders()); // ⬅️ même URL que urls.py
}

updateProfilEmploye(fd: FormData) {
  const token = localStorage.getItem('access_token') || localStorage.getItem('access token') || '';
  const headers = { Authorization: `Bearer ${token}` }; // ne pas fixer Content-Type pour FormData
  return this.http.patch(`${this.apiUrl}/profil-employe/update/`, fd, { headers });
}

uploadAvatar(file: File) {
  const form = new FormData();
  form.append('avatar', file, file.name);
  return this.http.post(`${this.apiUrl}/profil-employe/avatar/`, form, this.getAuthHeaders());
}

  /** ✅ Notifie tous les abonnés qu'un rechargement est nécessaire */
  triggerReload() {
    this.reloadSubject.next();
  }
}

