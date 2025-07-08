import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({ providedIn: 'root' })
export class EmployeService {
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

  // ✏️ Modifier un suivi
  modifierSuivi(id: number, suivi: any): Observable<any> {
     const token = localStorage.getItem('access_token'); // ou 'token' selon ton projet
  const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
  });
    return this.http.put(`${this.apiUrl}/modifier-suivi/${id}/`, {suivi}, { headers });
  }

 

  /** ✅ Notifie tous les abonnés qu'un rechargement est nécessaire */
  triggerReload() {
    this.reloadSubject.next();
  }
}

