import { Component, OnInit } from '@angular/core';
import { AuthService, DecodedToken } from 'src/app/services/auth/auth.service';
import { OffreService } from 'src/app/services/offre/offre.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { UploadService } from 'src/app/services/upload/upload.service';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ProfilService } from 'src/app/services/profil/profil.service';
import { ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';




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
  profilCandidat: any = null;
  profilComplet: boolean = false;
  dejaPostulee: boolean = false;

  constructor(
    private offreService: OffreService,
    private uploadService: UploadService,
    private authService: AuthService,
    private http: HttpClient,
    private router: Router,
    private profilService:ProfilService,
     private route: ActivatedRoute
  ) {}

ngOnInit(): void {
  this.user = this.authService.getUserInfo();
  this.isLoggedIn = !!this.user;


  const token = localStorage.getItem('access_token');
  const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
  });

  // Étape 1 : récupérer candidat_id
  this.http.get(`${environment.apiUrl}/get-candidat-id/`, { headers }).subscribe({
    next: (res: any) => {
      this.candidatId = res.candidat_id;

      // Étape 2 : récupérer profil
      this.profilService.getProfil().subscribe({
        next: (profil) => {
          this.profilCandidat = profil;
          this.profilComplet = !this.profilService.isProfilIncomplet(profil);

          // Étape 3 : vérifier postulation si offre déjà sélectionnée
          if (this.selectedOffer) {
            this.verifierSiDejaPostulee();
          }
        },
        error: (err) => {
          console.error("Erreur lors de la récupération du profil :", err);
        }
      });
    },
    error: (err) => {
      console.error("Erreur lors de la récupération de candidat_id :", err);
    }
  });



    this.chargerOffres();
     // Attendre un petit délai pour s'assurer que les offres sont bien chargées
  setTimeout(() => {
    this.route.queryParams.subscribe(params => {
      const offreId = params['offreId'];
      if (offreId) {
        const found = this.offres.find(o => o.id == offreId);
        if (found) {
          this.selectOffer(found);
        }
      }
    });
  }, 500); // délai léger pour éviter que this.offres soit vide

    this.filteredOffres = [...this.offres];
    this.updatePagination();
  }

chargerOffres() {
  this.offreService.getAllOffres().subscribe({
    next: (data) => {
      this.offres = data ?? [];
      this.sortNewestFirst(this.offres); // ✅ le plus récent d’abord

      // si un offreId arrive en query param, on le privilégie
      const qid = this.route.snapshot.queryParamMap.get('offreId');
      if (qid) {
        const found = this.offres.find(o => String(o.id) === String(qid));
        if (found) this.selectedOffer = found;
      }

      this.updatePagination();

      // si rien sélectionné, on prend la 1ère (la plus récente)
      if (!this.selectedOffer && this.paginatedOffres.length) {
        this.selectOffer(this.paginatedOffres[0]);
      }
    },
    error: (err) => {
      console.error('Erreur lors du chargement des offres', err);
    }
  });
}

@ViewChild('cvInput') cvInput!: ElementRef;

handlePostulerClick() {
  if (!this.isLoggedIn) {
    alert("Veuillez vous connecter pour postuler.");
    this.router.navigate(['/auth/login']);
    return;
  }

  if (!this.profilComplet) {
    alert("Veuillez d'abord compléter votre profil avant de postuler.");
    localStorage.setItem('pending_offre_id', this.selectedOffer.id.toString());
    this.router.navigate(['/mon-profil']);
    return;
  }

  if (!this.selectedOffer) {
    alert("Veuillez d'abord sélectionner une offre.");
    return;
  }

  // ✅ Ouvre le sélecteur de fichier
  this.cvInput.nativeElement.click();
}

selectOffer(offer: any) {
  this.selectedOffer = offer;

  // 🔁 Vérifie si le candidat a déjà postulé
  if (this.candidatId) {
    this.verifierSiDejaPostulee();
  }
}


onFileSelected(event: any) {
  const file: File = event.target.files[0];
  if (!file) return;


  // 🔐 Vérifie si l'utilisateur est connecté
  if (!this.authService.getUserInfo()) {
    alert("Veuillez vous connecter pour déposer votre CV.");
    this.router.navigate(['/auth/login']); // redirection vers login
    return;
  }

   // 🟡 Vérifie si le profil est incomplet
  if (!this.profilComplet) {
    alert("Veuillez d’abord compléter votre profil avant de déposer un CV.");
    this.router.navigate(['/mon-profil']);
    return;
  }

  // ✅ Vérifie que l'offre est sélectionnée
  if (!this.selectedOffer || !this.candidatId) {
    alert("Veuillez d'abord sélectionner une offre.");
    return;
  }

  const offreId = this.selectedOffer.id;

  this.uploadService.uploadCV(file, offreId, this.candidatId).subscribe({
    next: () => {
      alert("✅ CV déposé avec succès !");
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
      (offre.titre || '').toLowerCase().includes(term) ||
      (offre.description || '').toLowerCase().includes(term)
    );
  }

  this.page = 1;
  this.updatePagination(); // ↦ auto-sélection dans updatePagination()
}

onSearchSubmit(e: Event) {
  e.preventDefault();
  this.filterOffres();
}


private sortNewestFirst(list: any[]) {
  list.sort((a, b) => {
    const da = Date.parse(a?.created_at || a?.date_publication || '');
    const db = Date.parse(b?.created_at || b?.date_publication || '');
    if (!Number.isNaN(db - da)) return db - da;     // on a des dates valides
    return (b?.id ?? 0) - (a?.id ?? 0);             // fallback par id
  });
}

trackById(_i: number, item: any) { return item?.id; }

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
verifierSiDejaPostulee() {
  if (!this.candidatId || !this.selectedOffer) return;

  const token = localStorage.getItem('access_token');
  const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
  });

  this.http.get<any>(
    `${environment.apiUrl}/candidatures/dejapostule/${this.selectedOffer.id}/`,
    { headers }
  ).subscribe({
    next: (res) => {
      this.dejaPostulee = res.dejapostule;
    },
    error: (err) => {
      console.error("Erreur lors de la vérification de postulation :", err);
       this.dejaPostulee = false;
    }
  });
}





}
