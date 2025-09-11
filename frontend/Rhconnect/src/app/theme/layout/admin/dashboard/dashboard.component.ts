import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SharedModule } from 'src/app/theme/shared/shared.module';
declare const AmCharts;
import dataJson from 'src/fake-data/map_data';
import mapColor from 'src/fake-data/map-color-data.json';
import { OffreService } from 'src/app/services/offre/offre.service';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from 'src/app/services/auth/auth.service';
import { EmployeService } from 'src/app/services/employe/employe.service';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, SharedModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  candidatures: any[] = [];
  filtrerEnAttente: boolean = true;
  role: string = '';
  selectedOffre: string = '';
  selectedStatut: string = '';
  kpis : any[] = [];
  kpiPieData: number[] = [];
  kpiTopOffers: any[] = [];
  kpiMatchingAvg: { offre: string, avg: number }[] = [];

  constructor(private offreService: OffreService, private toastr:ToastrService,  private authService: AuthService,  private employeService: EmployeService,){}
  // life cycle event
   ngOnInit(): void {
    const userInfo = this.authService.getUserInfo();
    this.role = userInfo?.role || '';

    const api$ = this.role === 'gestionnaire_rh'
      ? this.offreService.getCandidaturesGestionnaire()
      : this.offreService.getCandidatures();

    api$.subscribe(data => {
      this.candidatures = data.sort((a: any, b: any) => b.score - a.score);

      // ✅ Initialiser mes KPI
      this.initKpis();
      this.initCharts();
    });
  }

  initKpis(): void {
    // Total
    const total = this.candidatures.length;

    // Répartition
    const accepted = this.candidatures.filter(c => c.statut === 'ACCEPTEE').length;
    const rejected = this.candidatures.filter(c => c.statut === 'REJETEE').length;
    const pending = this.candidatures.filter(c => c.statut === 'EN_ATTENTE').length;
    this.kpiPieData = [accepted, rejected, pending];

    // Top postes attractifs
    const counts: any = {};
    this.candidatures.forEach(c => {
      counts[c.offre] = (counts[c.offre] || 0) + 1;
    });
    this.kpiTopOffers = Object.entries(counts).sort((a: any, b: any) => b[1] - a[1]).slice(0, 5);

/* Matching IA moyen PAR OFFRE → bloc rating dynamique */
 const scores: { [key: string]: number[] } = {};
    this.candidatures.forEach(c => {
      if (!scores[c.offre]) scores[c.offre] = [];
      scores[c.offre].push(Number(c.score));
    });
    this.kpiMatchingAvg = Object.entries(scores).map(([offre, vals]: any) => ({
      offre,
      avg: parseFloat((vals.reduce((a: any, b: any) => a + b, 0) / vals.length).toFixed(1))
    }));

    const validThisMonth = this.candidatures.filter(c =>
      c.statut === 'ACCEPTEE' &&
      new Date(c.date_validation).getMonth() === new Date().getMonth() &&
      new Date(c.date_validation).getFullYear() === new Date().getFullYear()
    ).length;


    // ✅ Remplir le tableau KPI pour affichage
    this.kpis = [
      {
        title: '📊 Total Candidatures',
        value: total,
        description: 'Nombre total de candidatures',
        icon: 'feather icon-users text-c-blue',
      },
      {
        title: '🎯 Pipeline Recrutement',
        value: `${accepted} ✅ | ${rejected} ❌ | ${pending} ⏳`,
        description: 'Répartition par statut',
        icon: 'feather icon-pie-chart text-c-green',
      },

      {
        title: '📅 Recrutements validés (mois)',
        value: validThisMonth,
        description: 'Recrutements confirmés ce mois-ci',
        icon: 'feather icon-check-circle text-c-pink',
      },
    ];
  }

  initCharts(): void {
    // ✅ Pie chart pipeline
    setTimeout(() => {
      AmCharts.makeChart('kpiPieChart', {
        type: 'pie',
        theme: 'light',
        dataProvider: [
          { statut: 'Acceptée', value: this.kpiPieData[0] },
          { statut: 'Rejetée', value: this.kpiPieData[1] },
          { statut: 'En attente', value: this.kpiPieData[2] },
        ],
        titleField: 'statut',
        valueField: 'value',
        balloon: { fixedPosition: true }
      });

   AmCharts.makeChart('kpiTopOffersChart', {
  type: 'serial',
  theme: 'light',
  dataProvider: this.kpiTopOffers.map(([offre, count]) => ({ offre, count })),
  categoryField: 'offre',
  graphs: [{
    type: 'column',
    valueField: 'count',
    fillAlphas: 0.8,
    balloonText: '[[category]] : [[value]]'
  }],
  categoryAxis: {
    gridPosition: 'start',
    labelRotation: 30,
    autoWrap: true,
    fontSize: 12
  }
});
    }, 300);
  }
// updateLabel(id: number, label: number) {
//   this.offreService.updateLabel(id, label).subscribe({
//     next: () => {
//       console.log("✅ Label mis à jour");
//     },
//     error: (err) => {
//       console.error("❌ Erreur lors de la mise à jour du label", err);
//     }
//   });
// }

 updateStatut(id: number, statut: string): void {
    this.offreService.updateStatut(id, statut).subscribe(() => {
      const index = this.candidatures.findIndex(c => c.id === id);
      if (index !== -1) this.candidatures[index].statut = statut;
    });
  }
  get offresDisponibles(): string[] {
  return [...new Set(this.candidatures.map(c => c.offre))];
}
  trackByOffre(index: number, offre: string): string {
  return offre;
}

get candidaturesFiltrees(): any[] {
  let result = this.candidatures;

  // ✅ Filtrer par offre si sélectionnée
  if (this.selectedOffre) {
    result = result.filter(c => c.offre === this.selectedOffre);
  }

  // ✅ Si un statut est sélectionné explicitement
  if (this.selectedStatut) {
    result = result.filter(c => c.statut === this.selectedStatut);

  }

  return result;
}


    getScoreClass(score: number): string {
    if (score >= 60) return 'badge bg-success';
    if (score >= 40) return 'badge bg-warning text-dark';
    return 'badge bg-danger';
  }
confirmerEmbauche(id: number): void {
  this.offreService.confirmerEmbauche(id).subscribe({
    next: (res: any) => {
      // ✅ Affiche le message de succès
      this.toastr.success(res.message || 'Candidat embauché.');

      // ✅ Retire le candidat de la liste affichée
      this.candidatures = this.candidatures.filter(c => c.id !== id);
      this.employeService.triggerReload();
    },
    error: (err) => this.toastr.error(err.error?.error || 'Erreur')
  });
}
resetFiltres(): void {
  this.selectedOffre = '';
  this.selectedStatut = '';
  this.filtrerEnAttente = true;
}


}
