import { Component, OnInit } from '@angular/core';
import { OffreService } from 'src/app/services/offre/offre.service';
import { SharedModule } from 'src/app/theme/shared/shared.module';
import { RouterModule } from '@angular/router'; 

@Component({
  selector: 'app-liste-offre',
  imports: [SharedModule, RouterModule],
  templateUrl: './liste-offre.component.html',
  styleUrl: './liste-offre.component.scss'
})
export class ListeOffreComponent implements OnInit {
  offres: any[] = [];

  constructor(private offreService: OffreService) {}

  ngOnInit(): void {
    this.offreService.getAllOffres().subscribe({
      next: (res) => {
        this.offres = res;  // res = uniquement les offres du recruteur
      },
      error: (err) => {
        console.error('Erreur chargement des offres', err);
      }
    });
  }
  supprimerOffre(id: number) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette offre ?')) {
      this.offreService.supprimerOffre(id).subscribe({
        next: () => {
          this.offres = this.offres.filter(o => o.id !== id);
          alert('Offre supprimée avec succès.');
        },
        error: () => {
          alert('Erreur lors de la suppression.');
        }
      });
    }
  }
  
}

