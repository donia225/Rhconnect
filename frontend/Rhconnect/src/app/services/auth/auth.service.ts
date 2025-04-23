import { HttpClient, HttpHeaders  } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from 'src/environments/environment';
import { BehaviorSubject } from 'rxjs';
import { throwError } from 'rxjs';


export interface DecodedToken {
  id: number;
  username:string;
  nom: string;
  prenom: string;
  email: string;
  role: string;
  exp: number;
}
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private userSubject = new BehaviorSubject<DecodedToken | null>(this.getDecodedToken());
  public user$ = this.userSubject.asObservable();
  

  private apiUrl = environment.apiUrl;
  constructor(private http: HttpClient) { }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register/`, userData);
  }
   login(credentials: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/login/`, credentials).pipe(
      tap((res: any) => {
        localStorage.setItem('access_token', res.token);
        localStorage.setItem('refresh_token', res.refresh);
        localStorage.setItem('user_info', JSON.stringify(res.user));
        this.userSubject.next(res.user); // 🔥 Met à jour l’état
      })
    );
  }
  getCandidatId(): Observable<any> {
    const token = localStorage.getItem('access_token');
  
    if (!token) {
      console.error("Pas de token !");
      return throwError(() => new Error("Token manquant"));
    }
  
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });
  
    return this.http.get(`${this.apiUrl}/get-candidat-id/`, { headers });
  }

  refreshToken(refresh: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/token/refresh/`, { refresh });
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    this.userSubject.next(null); // 🔥 Déconnexion propre
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }
  getDecodedToken(): DecodedToken | null {
    const token = this.getToken();
    if (!token) return null;
    try {
      const payloadBase64 = token.split('.')[1];
      const decodedPayload = atob(payloadBase64);
      return JSON.parse(decodedPayload);
    } catch (e) {
      console.error('Token invalide', e);
      return null;
    }
  }
  getUserInfo(): DecodedToken | null {
    const user = localStorage.getItem('user_info');
    return user ? JSON.parse(user) : null;
  }
  
  
}