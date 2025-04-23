import { CommonModule } from '@angular/common';
import { Component, AfterViewInit, OnInit } from '@angular/core';
import { AuthService, DecodedToken } from 'src/app/services/auth/auth.service';
import { OffreService } from 'src/app/services/offre/offre.service';
import { UploadService } from 'src/app/services/upload/upload.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';
declare var AOS: any;

@Component({
  selector: 'app-accueil',
  imports: [CommonModule],
  templateUrl: './accueil.component.html',
  styleUrl: './accueil.component.scss'
})
export class AccueilComponent implements AfterViewInit, OnInit {
  user: DecodedToken | null = null;
  isLoggedIn: boolean = false;
  activeTab: string = 'accueil';
  selectedFile: File | null = null;
  selectedOffer: any = null;
  selectedOfferIndex: number | null = null;
  offres: any[] = [];
  candidatId: number | null = null;


  constructor(
    private authService: AuthService,
    private offreService: OffreService,
    private uploadService: UploadService,
    private http: HttpClient
  ) {}

  ngAfterViewInit(): void {
    AOS.init();

    const links = document.querySelectorAll('.nav-link.scrollto');
    links.forEach(link => {
      link.addEventListener('click', function () {
        links.forEach(l => l.classList.remove('active'));
        this.classList.add('active');
      });
    });
  }

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
  }
  

  chargerOffres() {
    this.offreService.getAllOffres().subscribe({
      next: (data) => {
        this.offres = data;
      },
      error: (err) => {
        console.error('Erreur lors du chargement des offres', err);
      }
    });
  }

  logout() {
    this.authService.logout();
    window.location.reload();
  }

  setActiveTab(tab: string) {
    this.activeTab = tab;
  }

  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (!file) return;
  
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      alert("Formats acceptés : PDF, JPG, PNG, DOC, DOCX");
      return;
    }
  
    if (this.selectedOfferIndex === null || !this.candidatId) {
      alert("Veuillez d'abord sélectionner une offre et vous connecter.");
      return;
    }
    
    const offreId = this.offres[this.selectedOfferIndex].id;
    
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

  selectOffer(index: number) {
    this.selectedOfferIndex = index;
  }
}