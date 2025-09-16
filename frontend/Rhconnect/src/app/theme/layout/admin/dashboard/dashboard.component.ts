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
  currentPage = 1;
  pageSize = 10;                 
  paginateRecruiter = true; 
  validatedThisMonth = 0;
  private pieChart: any;

  constructor(private offreService: OffreService, private toastr:ToastrService,  private authService: AuthService,  private employeService: EmployeService,){}
  // life cycle event
   ngOnInit(): void {
    const userInfo = this.authService.getUserInfo();
    this.role = userInfo?.role || '';
    this.pageSize = (this.role === 'gestionnaire_rh') ? 10 : 25;
    if (this.role === 'gestionnaire_rh') {
    this.selectedStatut = 'ACCEPTEE';
  }
    const api$ = this.role === 'gestionnaire_rh'
      ? this.offreService.getCandidaturesGestionnaire()
      : this.offreService.getCandidatures();

    api$.subscribe(data => {
       this.candidatures = (data || []).sort(
    (a: any, b: any) => (this.parseScore(b.ai_score ?? b.score) || 0) -
                        (this.parseScore(a.ai_score ?? a.score) || 0)
  );
      
  if (this.role === 'gestionnaire_rh') this.fetchValidatedThisMonth();  // ✅
  this.refreshKpis();

      // ✅ Initialiser mes KPI
      this.initKpis();
      this.initCharts();
    });
  }
  get usePagination(): boolean {
  return this.role === 'gestionnaire_rh' || this.paginateRecruiter;
}
onOffreChange()  { this.currentPage = 1; this.initKpis(); }
onStatutChange() { this.currentPage = 1; this.initKpis(); }
private parseScore(raw: any): number {
  if (raw == null) return NaN;

  // chaîne: "82,5%", "85", "0.82"
  if (typeof raw === 'string') {
    const m = raw.match(/-?\d+(?:[.,]\d+)?/);   // extrait la partie numérique
    if (!m) return NaN;
    const n = Number(m[0].replace(',', '.'));
    return Number.isFinite(n) ? (n <= 1 ? n * 100 : n) : NaN;
  }

  // nombre: 0.82, 82
  if (typeof raw === 'number') {
    return raw <= 1 ? raw * 100 : raw;
  }

  return NaN;
}


  initKpis(): void {
    const source = this.candidaturesFiltrees; 

    // Répartition
    const accepted = this.candidatures.filter(c => c.statut === 'ACCEPTEE').length;
    const rejected = this.candidatures.filter(c => c.statut === 'REJETEE').length;
    const pending = this.candidatures.filter(c => c.statut === 'EN_ATTENTE').length;
    this.kpiPieData = [accepted, rejected, pending];

    // Top postes attractifs
      const counts: Record<string, number> = {};
    this.candidatures.forEach(c => {
      counts[c.offre] = (counts[c.offre] || 0) + 1;
    });
    this.kpiTopOffers = Object.entries(counts).sort((a: any, b: any) => b[1] - a[1]).slice(0, 5);

/* Matching IA moyen PAR OFFRE → bloc rating dynamique */
 const scores: Record<string, number[]> = {};
   const buckets: Record<string, number[]> = {};
  this.candidatures.forEach(c => {
    const s = this.parseScore(c.ai_score ?? c.score);
    if (Number.isFinite(s)) (buckets[c.offre] ||= []).push(s);
  });

  this.kpiMatchingAvg = Object.entries(buckets).map(([offre, vals]) => {
    const avg = vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : 0;
    return { offre, avg }; // en %
  }).sort((a,b) => b.avg - a.avg);
   this.refreshCharts(); 
}
 

    // ✅ Remplir le tableau KPI pour affichage
  private refreshKpis(): void {
  const total = this.candidatures.length;
  const accepted = this.candidatures.filter(c => c.statut === 'ACCEPTEE').length;
  const rejected = this.candidatures.filter(c => c.statut === 'REJETEE').length;
  const pending  = this.candidatures.filter(c => c.statut === 'EN_ATTENTE').length;

  this.kpis = [
    { title: '📊 Total Candidatures', value: total, description: 'Nombre total de candidatures', icon: 'feather icon-users text-c-blue' },
    { title: '🎯 Pipeline Recrutement', value: `${accepted} ✅ | ${rejected} ❌ | ${pending} ⏳`, description: 'Répartition par statut', icon: 'feather icon-pie-chart text-c-green' },
    { title: '📅 Recrutements validés (mois)', value: this.validatedThisMonth, description: 'Recrutements confirmés ce mois-ci', icon: 'feather icon-check-circle text-c-pink' },
  ];
}

private fetchValidatedThisMonth(): void {
  this.employeService.getEmployes().subscribe({
    next: (emps: any[]) => {
      const now = new Date();
      this.validatedThisMonth = (emps || []).filter(e => {
        const d = new Date(e.date_embauche);   // <-- le serializer renvoie date_embauche
        return !isNaN(d.getTime())
            && d.getMonth() === now.getMonth()
            && d.getFullYear() === now.getFullYear();
      }).length;
      this.refreshKpis(); // reconstruit les cartes avec la nouvelle valeur
    },
    error: () => {
      this.validatedThisMonth = 0;
      this.refreshKpis();
    }
  });
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
  private refreshCharts(): void {
  if (!this.pieChart) return;
  this.pieChart.dataProvider = [
    { statut: 'Acceptée', value: this.kpiPieData[0] },
    { statut: 'Rejetée', value: this.kpiPieData[1] },
    { statut: 'En attente', value: this.kpiPieData[2] },
  ];
  this.pieChart.validateData();
}


private parseDate(raw: any): Date | null {
  if (!raw) return null;
  const s = String(raw);
  let d = new Date(s);
  if (!isNaN(d.getTime())) return d;

  const n = Number(s);
  if (Number.isFinite(n)) {
    d = new Date(n > 1e12 ? n : n * 1000); // ms ou s
    if (!isNaN(d.getTime())) return d;
  }
  return null;
}

private byNewestDesc = (a: any, b: any): number => {
  const ad = this.parseDate(a.created_at || a.createdAt || a.submitted_at || a.date);
  const bd = this.parseDate(b.created_at || b.createdAt || b.submitted_at || b.date);
  if (ad && bd && bd.getTime() !== ad.getTime()) return bd.getTime() - ad.getTime();
  if (ad && !bd) return -1;
  if (!ad && bd) return 1;
  // fallback sur id décroissant
  if (typeof a.id === 'number' && typeof b.id === 'number' && a.id !== b.id) return b.id - a.id;
  return 0;
};


 updateStatut(id: number, statut: string): void {
    this.offreService.updateStatut(id, statut).subscribe(() => {
      const index = this.candidatures.findIndex(c => c.id === id);
      if (index !== -1) this.candidatures[index].statut = statut;
       this.initKpis();
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
  if (this.selectedOffre) result = result.filter(c => c.offre === this.selectedOffre);
  if (this.selectedStatut) result = result.filter(c => c.statut === this.selectedStatut);
  return result.slice().sort(this.byNewestDesc); // ← tri “plus récentes d’abord”
}

get candidaturesFiltreesPaged(): any[] {
  const arr = this.candidaturesFiltrees;
 if (!this.usePagination) return arr;  // recruteur sans pagination => tout
  const start = (this.currentPage - 1) * this.pageSize;
  return arr.slice(start, start + this.pageSize);
}
get totalPages(): number {
  return Math.max(1, Math.ceil(this.candidaturesFiltrees.length / this.pageSize));
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
  if (!this.usePagination) return;
  const page = Number(p);
  if (!Number.isFinite(page)) return;
  if (page < 1 || page > this.totalPages || page === this.currentPage) return;
  this.currentPage = page;
}




  trackById(_i: number, c: any) { return c.id; }


    getScoreClass(score: number): string {
    if (score >= 70) return 'badge bg-success';
    if (score < 70) return 'badge bg-warning text-dark';
    return 'badge bg-danger';
  }
confirmerEmbauche(id: number): void {
  this.offreService.confirmerEmbauche(id).subscribe({
    next: (res: any) => {
      // ✅ Affiche le message de succès
      this.toastr.success(res.message || 'Candidat embauché.');

      // ✅ Retire le candidat de la liste affichée
      this.candidatures = this.candidatures.filter(c => c.id !== id);
      this.validatedThisMonth += 1;
      this.refreshKpis();
      this.initKpis();

      this.employeService.triggerReload();
    },
    error: (err) => this.toastr.error(err.error?.error || 'Erreur')
  });
}
get hasEmbauchables(): boolean {
  return this.candidaturesFiltrees.some(c => c.statut === 'ACCEPTEE');
}

resetFiltres(): void {
  this.selectedOffre = '';
  this.selectedStatut = (this.role === 'gestionnaire_rh') ? 'ACCEPTEE' : '';
  this.currentPage = 1;
  this.initKpis();
}


}
