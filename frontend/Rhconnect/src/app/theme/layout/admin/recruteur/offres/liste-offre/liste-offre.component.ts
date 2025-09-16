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
  selectedOffre: any = null;
  modalVisible = false;
  currentPage = 1;
  pageSize = 5;

  constructor(private offreService: OffreService) {}

 ngOnInit(): void {
  this.offreService.getMesOffres().subscribe({
    next: (res: any[]) => {
      // tri : plus récentes d’abord
      const byNewest = (a: any, b: any) => {
        const ta = new Date(a?.date_publication ?? a?.date ?? 0).getTime();
        const tb = new Date(b?.date_publication ?? b?.date ?? 0).getTime();
        return tb - ta;
      };

      this.offres = (res ?? [])
        .slice()                 // copie défensive
        .sort(byNewest)          // tri
        .map((o: any) => ({      // enrichit chaque offre
          ...o,
          _skills: String(o?.competences ?? '')
            .split(',')
            .map((s: string) => s.trim())
            .filter((s: string) => s.length > 0),
        }));
    },
    error: (err) => console.error('Erreur chargement des offres', err),
  });
}

   get offresPaged(): any[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.offres.slice(start, start + this.pageSize);
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.offres.length / this.pageSize));
  }

  get paginationRange(): (number | string)[] {
    const total = this.totalPages, cur = this.currentPage, delta = 2;
    const out: (number | string)[] = [];
    const start = Math.max(1, cur - delta);
    const end   = Math.min(total, cur + delta);
    if (start > 1) { out.push(1); if (start > 2) out.push('…'); }
    for (let p = start; p <= end; p++) out.push(p);
    if (end < total) { if (end < total - 1) out.push('…'); out.push(total); }
    return out;
  }

  goPage(p: number | string): void {
    const page = Number(p);
    if (!Number.isFinite(page)) return;
    if (page < 1 || page > this.totalPages || page === this.currentPage) return;
    this.currentPage = page;
  }


  supprimerOffre(id: number) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette offre ?')) return;
    this.offreService.supprimerOffre(id).subscribe({
      next: () => {
        this.offres = this.offres.filter(o => o.id !== id);
        // recaler la page si la liste a rétréci
        const maxPage = Math.max(1, Math.ceil(this.offres.length / this.pageSize));
        if (this.currentPage > maxPage) this.currentPage = maxPage;
        alert('Offre supprimée avec succès.');
      },
      error: () => alert('Erreur lors de la suppression.')
    });
  }
  ouvrirModal(offre: any): void {
  this.selectedOffre = offre;
  this.modalVisible = true;
}

fermerModal(): void {
  this.modalVisible = false;
  this.selectedOffre = null;
}
  
}

