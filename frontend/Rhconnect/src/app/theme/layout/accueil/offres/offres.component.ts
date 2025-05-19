import { Component, OnInit } from '@angular/core';
import { AuthService, DecodedToken } from 'src/app/services/auth/auth.service';
import { OffreService } from 'src/app/services/offre/offre.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { UploadService } from 'src/app/services/upload/upload.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-offres',
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './offres.component.html',
  styleUrls: ['./offres.component.scss']
})
export class OffresComponent implements OnInit {
  offres: any[] = [];
  selectedOffer: any = null;
  selectedFile: File | null = null;
  candidatId: number | null = null;
  isLoggedIn: boolean = false;
  user: DecodedToken | null = null;
  page = 1;
  pageSize = 4;
  totalPages = 1;
  pages: number[] = [];
  paginatedOffres: any[] = [];
  searchTerm: string = '';
  filteredOffres: any[] = [];

  constructor(
    private offreService: OffreService,
    private uploadService: UploadService,
    private authService: AuthService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.user = this.authService.getUserInfo();
    this.isLoggedIn = !!this.user;

    if (this.isLoggedIn) {
      const token = localStorage.getItem('access_token');
      const headers = new HttpHeaders({
        Authorization: `Bearer ${token}`
      });
      this.http.get(`${environment.apiUrl}/get-candidat-id/`, { headers }).subscribe({
        next: (res: any) => {
          this.candidatId = res.candidat_id;
        },
        error: (err) => {
          console.error(err);
          alert("Erreur lors de la récupération du profil candidat.");
        }
      });
    }

    this.chargerOffres();
    this.filteredOffres = [...this.offres];
    this.updatePagination();
  }

  chargerOffres() {
    this.offreService.getAllOffres().subscribe({
      next: (data) => {
        this.offres = data;
         this.updatePagination();
      },
      error: (err) => {
        console.error('Erreur lors du chargement des offres', err);
      }
    });
  }

selectOffer(offer: any) {
  this.selectedOffer = offer;
}


  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (!file) return;

    const allowedTypes = [
      'application/pdf', 'image/jpeg', 'image/png',
      'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    if (!allowedTypes.includes(file.type)) {
      alert("Formats acceptés : PDF, JPG, PNG, DOC, DOCX");
      return;
    }

    if (!this.selectedOffer || !this.candidatId)  {
      alert("Veuillez d'abord sélectionner une offre et vous connecter.");
      return;
    }

      const offreId = this.selectedOffer.id;

    this.uploadService.uploadCV(file, offreId, this.candidatId).subscribe({
      next: () => {
        alert("CV déposé avec succès !");
      },
      error: (err) => {
        console.error("Erreur d'upload du CV :", err);
        alert("Erreur lors du dépôt du CV.");
      }
    });
  }
  filterOffres() {
  const term = this.searchTerm.trim().toLowerCase();

  if (!term) {
    this.filteredOffres = [...this.offres];
  } else {
    this.filteredOffres = this.offres.filter(offre =>
      offre.titre.toLowerCase().includes(term) ||
      offre.description.toLowerCase().includes(term)
    );
  }
  this.selectedOffer = null;
  this.page = 1;
  this.updatePagination();
}
 updatePagination() {
  const source = this.filteredOffres.length ? this.filteredOffres : this.offres;

  this.totalPages = Math.ceil(source.length / this.pageSize);
  this.pages = Array.from({ length: this.totalPages }, (_, i) => i + 1);
  const start = (this.page - 1) * this.pageSize;
  const end = start + this.pageSize;

  this.paginatedOffres = source.slice(start, end);
}

goToPage(p: number, event?: Event) {
  if (event) event.preventDefault(); // 🔒 empêche le rechargement
  if (p < 1 || p > this.totalPages) return;
  this.page = p;
  this.updatePagination();
}
clearSearch() {
  this.searchTerm = '';
  this.filterOffres();
}


}
