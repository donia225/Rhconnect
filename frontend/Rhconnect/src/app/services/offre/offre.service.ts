
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';


@Injectable({
  providedIn: 'root'
})
export class OffreService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}


  ajouterOffre(offreData: any): Observable<any> {
    const headers = {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    };
    return this.http.post(`${this.apiUrl}/ajouter/`, offreData, headers);
  }
  
  getAllOffres(): Observable<any[]> {
    const headers = {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    };
    return this.http.get<any[]>(`${this.apiUrl}/offres/`, headers);
  }
  supprimerOffre(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/offres/${id}/`);
  }
  modifierOffre(id: number, offreData: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/offres/modifier/${id}/`, offreData);
  }
  getMesCandidatures(): Observable<any[]> {
    const headers = {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    };
  return this.http.get<any[]>(`${this.apiUrl}/mes-candidatures/`,  headers);
}
getCandidatures(): Observable<any> {
  const token = localStorage.getItem('access_token'); // ou 'token'
  const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
  });

  return this.http.get(`${this.apiUrl}/candidatures-recruteur`, { headers });
}


updateStatut(id: number, statut: string) {
  const token = localStorage.getItem('access_token'); // ou 'token' selon ton projet
  const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
  });

  return this.http.put(`${this.apiUrl}/candidature/${id}/update-statut`, { statut }, { headers });
}

}
