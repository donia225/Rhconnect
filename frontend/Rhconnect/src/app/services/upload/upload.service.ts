import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private apiUrl = `${environment.apiUrl}/upload-cv/`; // 🔄 à adapter côté Django

  constructor(private http: HttpClient) {}

uploadCV(file: File, offreId: number, candidatId: number): Observable<any> {
  const formData = new FormData();
  formData.append('cv', file);
  formData.append('offre', offreId.toString());
  formData.append('candidat', candidatId.toString()); // pas 'candidat_id'


  const token = localStorage.getItem('access_token');

  const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
  });

  return this.http.post(this.apiUrl, formData, { headers });
}

}
