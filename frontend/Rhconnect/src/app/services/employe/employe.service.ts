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

  /** ✅ Liste des suivis pour un employé */
  getSuivis(employeId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/employes/${employeId}/suivi/`, this.getAuthHeaders());
  }

  /** ✅ Ajouter un suivi carrière */
  addSuivi(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/suivis/`, data, this.getAuthHeaders());
  }

  /** ✅ Notifie tous les abonnés qu'un rechargement est nécessaire */
  triggerReload() {
    this.reloadSubject.next();
  }
}
